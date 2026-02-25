from fastapi import FastAPI, UploadFile, File, HTTPException, Depends,  BackgroundTasks
import fitz
import uuid
import os
from dotenv import load_dotenv
from supabase import create_client
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from jose import jwt
from services.analysis_engine import run_analysis_for_rapt

load_dotenv()

app = FastAPI()

# ---------------- CORS ---------------- #
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- SUPABASE ---------------- #
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase environment variables missing")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- PDF PARSER ---------------- #
def extract_text_from_pdf(file_bytes):
    try:
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")

# ---------------- BASIC ANALYSIS ---------------- #
def analyze_text(raw_text: str):

    skill_groups = {
        "programming": ["python", "java", "c++", "javascript"],
        "frontend": ["react", "html", "css"],
        "backend": ["fastapi", "node", "django"],
        "ml": ["machine learning", "tensorflow", "pytorch"]
    }

    text = raw_text.lower()
    found_skills = []
    score = 0

    for category, skills in skill_groups.items():
        for skill in skills:
            if skill in text:
                found_skills.append(skill)
                score += 15

    if len(found_skills) >= 5:
        score += 20

    return found_skills, score

# ---------------- AUTH ---------------- #

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        user = supabase.auth.get_user(token)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        return user.user.id

    except Exception as e:
        print("JWT ERROR:", e)
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------- ROUTES ---------------- #

@app.get("/")
def home():
    return {"status": "RAPT backend live 🚀"}

# ---------- UPLOAD RESUME ---------- #
@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        file_bytes = await file.read()
        file_id = str(uuid.uuid4())
        file_path = f"{file_id}.pdf"

        # Upload to Supabase Storage
        supabase.storage.from_("resumes").upload(
            file_path,
            file_bytes,
            {"content-type": "application/pdf"}
        )

        # Extract Text
        extracted_text = extract_text_from_pdf(file_bytes)

        print("\n===== PARSED RESUME TEXT =====\n")
        print(extracted_text[:1000])
        print("\n==============================\n")

        # Insert into DB
        supabase.table("resumes").insert({
            "id": file_id,
            "user_id": user_id,   # ⭐ FIXED
            "storage_path": file_path,
            "file_name": file.filename,
            "raw_text": extracted_text
        }).execute()

        return {
            "status": "success",
            "file_id": file_id,
            "message": "Resume processed successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- ANALYZE RESUME ---------- #
@app.post("/analyze-resume/{resume_id}")
def analyze_resume(
    resume_id: str,
    user_id: str = Depends(get_current_user)
):

    res = supabase.table("resumes").select("*").eq("id", resume_id).eq("user_id", user_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Resume not found")

    raw_text = res.data[0]["raw_text"]

    # ⭐ NEW AI ENGINE
    analysis = run_analysis_for_rapt(raw_text)

    supabase.table("analysis").insert({
        "resume_id": resume_id,
        "score": analysis["score"],
        "skills": analysis["skills"],
        "missing_skills": analysis["missing_skills"],
        "feedback_json": analysis["feedback_json"],
        "model_version": analysis["model_version"]
    }).execute()

    return {
        "resume_id": resume_id,
        "status": "analysis complete",
        "score": analysis["score"],
        "skills": analysis["skills"],
        "feedback": analysis["feedback_json"]
    }

@app.get("/analysis/{resume_id}")
def get_analysis(
    resume_id: str,
    user_id: str = Depends(get_current_user)
):

    res = (
        supabase
        .table("analysis")
        .select("*")
        .eq("resume_id", resume_id)
        .execute()
    )

    if not res.data:
        return None

    # return latest analysis
    return res.data[0]

@app.get("/profile")
def get_profile(user_id: str = Depends(get_current_user)):
    res = supabase.table("profiles").select("*").eq("id", user_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return res.data[0]

@app.get("/my-resumes")
def get_my_resumes(user_id: str = Depends(get_current_user)):

    res = supabase.table("resumes") \
        .select("*, analysis(*)") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()

    return res.data

@app.patch("/profile")
def update_profile(data: dict,
    user_id: str = Depends(get_current_user)):

    res = supabase.table("profiles") \
        .update(data) \
        .eq("id", user_id) \
        .execute()

    return res.data

# ---------- CREATE JOB (RECRUITER ONLY) ---------- #

from ml_models.ai_matcher import matcher

# ---------- BACKGROUND EMBEDDING WORKER ---------- #
def generate_job_embedding(job_id: str, description: str):
    try:
        embedding = matcher.get_embedding(description).tolist()

        supabase.table("jobs") \
            .update({"embedding": embedding}) \
            .eq("id", job_id) \
            .execute()

        print(f"✅ Embedding generated for job {job_id}")

    except Exception as e:
        print("❌ Embedding generation failed:", e)

@app.post("/jobs/create")
def create_job(
    job: dict,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):

    # 🔐 Check recruiter role
    profile = supabase.table("profiles") \
        .select("role") \
        .eq("id", user_id) \
        .single() \
        .execute()

    if not profile.data or profile.data["role"] != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can create jobs")

    company_id = job.get("company_id")

    # 🏢 Create company if needed
    if not company_id:

        company_name = job.get("company_name")
        if not company_name:
            raise HTTPException(status_code=400, detail="company_id or company_name required")

        company_insert = supabase.table("companies").insert({
            "name": company_name,
            "website": job.get("company_website"),
            "industry": job.get("company_industry")
        }).execute()

        company_id = company_insert.data[0]["id"]

    # 💾 Insert job FIRST (no embedding yet)
    res = supabase.table("jobs").insert({
        "company_id": company_id,
        "title": job["title"],
        "description": job["description"],
        "requirements": job.get("requirements", [])
    }).execute()

    job_id = res.data[0]["id"]

    # 🚀 Async embedding
    background_tasks.add_task(
        generate_job_embedding,
        job_id,
        job["description"]
    )

    return {
        "status": "success",
        "message": "Job created. Embedding generating in background.",
        "data": res.data
    }