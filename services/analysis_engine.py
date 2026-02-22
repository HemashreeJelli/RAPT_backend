import re
import json

# =========================================================
# 1. CONFIGURATION DATA
# =========================================================

SKILL_GROUPS = {
    "programming": ["python", "java", "c++", "javascript", "golang", "ruby", "typescript"],
    "frontend": ["react", "html", "css", "tailwind", "nextjs", "vue"],
    "backend": ["fastapi", "node", "django", "flask", "spring boot"],
    "ml": ["machine learning", "tensorflow", "pytorch", "scikit-learn", "nlp"],
    "database": ["postgresql", "mysql", "mongodb", "supabase", "redis", "oracle"]
}

SECTION_SYNONYMS = {
    "education": ["education", "academic", "university", "schooling", "qualifications"],
    "projects": ["projects", "personal work", "portfolio", "open source"],
    "experience": ["experience", "work history", "employment", "internship", "professional background"],
    "skills": ["skills", "technical stack", "competencies", "tools", "technologies"]
}

# Core ATS baseline skills
CORE_INDUSTRY_SKILLS = [
    "python", "react", "sql", "git", "aws", "docker", "api"
]


# =========================================================
# 2. SECTION DETECTION
# =========================================================

def detect_sections(text: str):
    """
    Detects presence of resume sections using synonym mapping.
    """
    lower_text = text.lower()
    results = {}

    for section, keywords in SECTION_SYNONYMS.items():
        results[section] = any(
            re.search(rf"\b{re.escape(kw)}\b", lower_text)
            for kw in keywords
        )

    return results


# =========================================================
# 3. SKILL EXTRACTION (ATS STYLE)
# =========================================================

def extract_skills(text: str):
    """
    Extract skills using regex word boundaries.
    Prevents false positives like 'c' matching 'cat'.
    """
    found = set()

    for category, skills in SKILL_GROUPS.items():
        for skill in skills:
            if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
                found.add(skill.lower())

    return list(found)


# =========================================================
# 4. SCORING SYSTEM
# =========================================================

def calculate_weighted_score(sections, skills, word_count):
    """
    Balanced ATS-style scoring:
    - 30% Structure
    - 50% Skill Density
    - 20% Formatting / Length
    """

    score = 0

    # -------- Structure Score (30 pts) --------
    present_sections = sum(1 for exists in sections.values() if exists)
    score += (present_sections / len(SECTIONSYNONYMS_SAFE())) * 30

    # -------- Skill Score (50 pts) --------
    skill_count = len(skills)

    if skill_count > 0:
        score += min(skill_count * 5, 50)

    # -------- Formatting Score (20 pts) --------
    if 300 <= word_count <= 800:
        score += 20
    elif word_count > 0:
        score += 10

    return round(score)


def SECTIONSYNONYMS_SAFE():
    """
    Prevent accidental mutation or missing dictionary.
    """
    return SECTION_SYNONYMS


# =========================================================
# 5. MASTER ANALYSIS ENGINE (ENGINE V2)
# =========================================================

def run_full_analysis(raw_text: str):
    """
    Main ATS Analysis Engine.
    Returns full structured analysis object.
    """

    # -------- Clean Text --------
    clean_text = " ".join(raw_text.split())
    word_count = len(clean_text.split())

    # -------- Analysis Steps --------
    sections = detect_sections(clean_text)
    found_skills = extract_skills(clean_text)

    # -------- Missing Core Skills --------
    missing_skills = [
        s for s in CORE_INDUSTRY_SKILLS
        if s not in found_skills
    ]

    # -------- Score --------
    ats_score = calculate_weighted_score(
        sections,
        found_skills,
        word_count
    )

    # -------- Feedback Generator --------
    feedback = {
        "strengths": [],
        "improvements": [],
        "ats_tips": [
            "Use standard fonts and avoid complex tables or graphics.",
            "Start bullet points with strong action verbs like 'Developed', 'Built', 'Designed'."
        ]
    }

    # Strengths Logic
    if ats_score >= 80:
        feedback["strengths"].append(
            "Excellent section structure and keyword density."
        )
    elif ats_score >= 50:
        feedback["strengths"].append(
            "Good start, but needs more specific technical keywords."
        )

    # Missing Sections Feedback
    for section, found in sections.items():
        if not found:
            feedback["improvements"].append(
                f"Missing '{section.capitalize()}' section."
            )

    # Missing Skills Feedback
    if missing_skills:
        feedback["improvements"].append(
            f"Consider adding core skills: {', '.join(missing_skills[:3])}"
        )

    # -------- FINAL ENGINE OUTPUT --------
    return {
        "status": "success",
        "score": ats_score,
        "word_count": word_count,
        "details": {
            "sections_found": [s for s, ok in sections.items() if ok],
            "skills_detected": found_skills,
            "missing_core_skills": missing_skills
        },
        "feedback": feedback,
        "engine_version": "2.1.0"
    }


# =========================================================
# 6. RAPT ADAPTER (IMPORTANT FOR YOUR FASTAPI DB)
# =========================================================

def run_analysis_for_rapt(raw_text: str):
    """
    Converts engine output into format expected by your FastAPI + Supabase DB.
    DO NOT CHANGE YOUR BACKEND LOGIC — this adapter handles compatibility.
    """

    result = run_full_analysis(raw_text)

    return {
        "score": result["score"],
        "skills": result["details"]["skills_detected"],
        "missing_skills": result["details"]["missing_core_skills"],
        "feedback_json": {
            "feedback": result["feedback"],
            "sections_found": result["details"]["sections_found"],
            "word_count": result["word_count"]
        },
        "model_version": result["engine_version"]
    }


# =========================================================
# 7. LOCAL TEST (OPTIONAL)
# =========================================================
if __name__ == "__main__":
    sample_resume = """
    Education: B.Tech Computer Science
    Skills: Python, React, SQL
    Experience: Built FastAPI backend
    """

    print(json.dumps(run_full_analysis(sample_resume), indent=2))