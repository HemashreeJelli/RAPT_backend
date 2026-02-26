from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
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

    # 🔎 Fetch resume
    res = (
        supabase
        .table("resumes")
        .select("*")
        .eq("id", resume_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Resume not found")

    raw_text = res.data[0]["raw_text"]

    # ⭐ Run AI analysis engine
    analysis = run_analysis_for_rapt(raw_text)

    # 💾 Save analysis FIRST (important)
    supabase.table("analysis").insert({
        "resume_id": resume_id,
        "score": analysis["score"],
        "skills": analysis["skills"],
        "missing_skills": analysis["missing_skills"],
        "feedback_json": analysis["feedback_json"],
        "model_version": analysis["model_version"]
    }).execute()

    # 🚀 Trigger resume embedding Edge Function
    try:
        r = requests.post(
            "https://uooknnnadspehbbmeudx.supabase.co/functions/v1/generate-resume-embedding",
            headers={
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            },
            json={
                "resume_id": resume_id,
                "skills": analysis["skills"],
                "feedback": analysis["feedback_json"],
                "score": analysis["score"]
            },
            timeout=10
        )

        print("🚀 Resume embedding triggered")
        print("RESUME EDGE STATUS:", r.status_code)
        print("RESUME EDGE RESPONSE:", r.text)

    except Exception as e:
        print("❌ Resume embedding trigger failed:", e)

    # ✅ Return response
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

# ---------- BACKGROUND EMBEDDING WORKER ---------- #


@app.post("/jobs/create")
def create_job(
    job: dict,
    user_id: str = Depends(get_current_user)
):

    # 🔐 recruiter check
    profile = supabase.table("profiles") \
        .select("role") \
        .eq("id", user_id) \
        .single() \
        .execute()

    if not profile.data or profile.data["role"] != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can create jobs")

    company_id = job.get("company_id")

    # 🏢 create company if missing
    if not company_id:
        company_insert = supabase.table("companies").insert({
            "name": job.get("company_name"),
            "website": job.get("company_website"),
            "industry": job.get("company_industry")
        }).execute()

        company_id = company_insert.data[0]["id"]

    # 💾 Insert job FIRST (without embedding)
    res = supabase.table("jobs").insert({
        "company_id": company_id,
        "title": job["title"],
        "description": job["description"],
        "requirements": job.get("requirements", [])
    }).execute()

    job_id = res.data[0]["id"]

    # 🚀 Trigger Edge Function to generate embedding
    try:
        r = requests.post(
            "https://uooknnnadspehbbmeudx.supabase.co/functions/v1/generate-embedding",
            headers={
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            },
            json={
                "job_id": job_id,
                "description": job["description"]
            },
            timeout=10
        )

        print("EDGE STATUS:", r.status_code)
        print("EDGE RESPONSE:", r.text)

        if r.status_code != 200:
            print("⚠️ Edge function returned non-200")

    except Exception as e:
        print("❌ Failed to trigger embedding:", e)

    return {
        "status": "success",
        "message": "Job created. Embedding generating via Edge Function.",
        "data": res.data
    }

@app.get("/recommended-jobs/{resume_id}")
def get_recommended_jobs(
    resume_id: str,
    user_id: str = Depends(get_current_user)
):

    # ===============================
    # 1️⃣ Get resume + embedding
    # ===============================
    resume_res = (
        supabase
        .table("resumes")
        .select("id, user_id, embedding")
        .eq("id", resume_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not resume_res.data:
        raise HTTPException(status_code=404, detail="Resume not found")

    embedding = resume_res.data.get("embedding")

    if not embedding:
        raise HTTPException(
            status_code=400,
            detail="Resume embedding not generated yet"
        )

    # ===============================
    # 2️⃣ Vector match
    # ===============================
    match_res = supabase.rpc(
        "match_jobs",
        {
            "query_embedding": embedding,
            "match_threshold": 0.3,
            "match_count": 10
        }
    ).execute()

    if not match_res.data:
        return []

    # ===============================
    # 3️⃣ Fetch resume analysis
    # ===============================
    resume_analysis = (
        supabase
        .table("analysis")
        .select("skills, score")
        .eq("resume_id", resume_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    resume_skills = []
    ats_score = 0

    if resume_analysis.data:
        resume_skills = resume_analysis.data[0]["skills"] or []
        ats_score = resume_analysis.data[0]["score"] or 0

    ats_norm = ats_score / 100  # normalize ATS

    # ===============================
    # 4️⃣ Fetch full job info
    # ===============================
    job_ids = [job["id"] for job in match_res.data]

    jobs_full = (
        supabase
        .table("jobs")
        .select("*, companies(*)")
        .in_("id", job_ids)
        .execute()
    )

    recommended = []

    for job in jobs_full.data:

        job_skills = job.get("requirements", []) or []

        # ------------------------------
        # 🧠 Skill overlap score
        # ------------------------------
        matched = [
            s for s in job_skills
            if s.lower() in [r.lower() for r in resume_skills]
        ]

        overlap_ratio = (
            len(matched) / len(job_skills)
            if job_skills else 0
        )

        # ------------------------------
        # 🧠 Get embedding similarity
        # ------------------------------
        similarity = next(
            (m["similarity"] for m in match_res.data if m["id"] == job["id"]),
            0.8
        )

        embedding_score = (1 - similarity)

        # ------------------------------
        # ⭐ HYBRID SCORE
        # ------------------------------
        hybrid_score = (
            embedding_score * 0.7 +
            overlap_ratio * 0.2 +
            ats_norm * 0.1
        )

        explanation = None
        if matched:
            explanation = (
                f"Recommended because your resume matches: "
                f"{', '.join(matched[:3])}"
            )

        recommended.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["companies"]["name"] if job.get("companies") else "",
            "match_score": round(hybrid_score * 100),
            "explanation": explanation
        })

    # ===============================
    # ⭐ SORT BY HYBRID SCORE
    # ===============================
    recommended.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    return recommended