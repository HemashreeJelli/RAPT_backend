from ml_models.ai_matcher import matcher
from services.supabase import supabase

# Fetch company ids
companies = supabase.table("companies").select("id,name").execute().data
company_ids = [c["id"] for c in companies]

jobs = [
{
"title": "Python Backend Developer",
"description": "We are looking for a backend developer experienced in Python and FastAPI to build scalable APIs. Experience with PostgreSQL and Docker preferred.",
"requirements": ["Python","FastAPI","PostgreSQL","REST APIs","Docker"]
},
{
"title": "React Frontend Engineer",
"description": "Seeking a frontend developer skilled in React.js to build modern responsive interfaces using hooks and API integrations.",
"requirements": ["React","JavaScript","CSS","UI/UX","API Integration"]
},
{
"title": "Machine Learning Intern",
"description": "Join our AI team to work on deep learning projects involving CNNs, TensorFlow, and data preprocessing.",
"requirements": ["Python","TensorFlow","CNN","Deep Learning","Data Processing"]
}
]

i = 0

for job in jobs:
    embedding = matcher.get_embedding(job["description"]).tolist()

    supabase.table("jobs").insert({
        "company_id": company_ids[i % len(company_ids)],
        "title": job["title"],
        "description": job["description"],
        "requirements": job["requirements"],
        "embedding": embedding
    }).execute()

    i += 1

print("✅ Jobs seeded successfully!")