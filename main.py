from fastapi import FastAPI, UploadFile, File, HTTPException
import fitz
import uuid
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase environment variables missing")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def extract_text_from_pdf(file_bytes):
    try:
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        file_bytes = await file.read()
        file_id = str(uuid.uuid4())
        file_path = f"{file_id}.pdf"

        # Upload to Supabase Storage
        storage_res = supabase.storage.from_("resumes").upload(
            file_path,
            file_bytes,
            {"content-type": "application/pdf"}
        )

        # Extract Text
        extracted_text = extract_text_from_pdf(file_bytes)

        # Insert into DB
        supabase.table("resumes").insert({
            "id": file_id,
            "user_id": None,
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
