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
    "database": ["postgresql", "mysql", "mongodb", "supabase", "redis", "oracle","sql"]
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

SECTION_WEIGHTS = {
    "skills": 0.30,
    "experience": 0.30,
    "projects": 0.25,
    "education": 0.15
}

ACTION_VERBS = [
    "developed", "built", "implemented",
    "designed", "created", "led"
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

# =========================================================
# NEW: SENIORITY ESTIMATION (ENGINE V3)
# =========================================================

def estimate_seniority(text, sections, skills):

    lower_text = text.lower()

    # ---- Detect experience signals ----
    internship_hits = len(re.findall(r"\b(intern|internship)\b", lower_text))
    company_hits = len(re.findall(r"\b(developer|engineer|worked at|company)\b", lower_text))

    # ---- Action verbs as maturity signal ----
    verb_hits = sum(1 for v in ACTION_VERBS if v in lower_text)

    skill_count = len(skills)

    # ---- Heuristic Logic ----
    if internship_hits == 0 and not sections.get("experience"):
        return "student"

    if internship_hits >= 1 and verb_hits < 3:
        return "student"

    if internship_hits >= 1 and verb_hits >= 3:
        return "junior"

    if company_hits >= 2 and verb_hits >= 5 and skill_count >= 8:
        return "mid"

    return "student"

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

# =========================================================
# NEW: SECTION LEVEL SCORING (ENGINE V3)
# =========================================================

def calculate_section_scores(text, sections, skills, word_count):

    lower_text = text.lower()

    # -------- Skills Score (0–25) --------
    skills_score = min(len(skills) * 3, 25)

    core_matches = len([s for s in CORE_INDUSTRY_SKILLS if s in skills])
    skills_score += core_matches * 2
    skills_score = min(skills_score, 25)

    # -------- Experience Score (0–25) --------
    experience_score = 0

    if sections.get("experience"):
        experience_score += 10

    verb_hits = sum(1 for v in ACTION_VERBS if v in lower_text)
    experience_score += min(verb_hits * 3, 15)

    # -------- Projects Score (0–25) --------
    projects_score = 0

    if sections.get("projects"):
        projects_score += 10

    if "github.com" in lower_text:
        projects_score += 5

    projects_score += min(len(skills), 10)
    projects_score = min(projects_score, 25)

    # -------- Education Score (0–25) --------
    education_score = 0

    if sections.get("education"):
        education_score += 15

    if re.search(r"\b(b\.?tech|bachelor|master|degree)\b", lower_text):
        education_score += 10

    return {
        "skills": skills_score,
        "experience": experience_score,
        "projects": projects_score,
        "education": education_score
    }

# =========================================================
# NEW: FINAL WEIGHTED SCORE (ENGINE V3)
# =========================================================

def calculate_resume_strength(section_scores):

    total = 0

    for section, weight in SECTION_WEIGHTS.items():
        total += section_scores[section] * weight

    # each section max = 25 → multiply to scale ~100
    return round(total * 4)


def SECTIONSYNONYMS_SAFE():
    """
    Prevent accidental mutation or missing dictionary.
    """
    return SECTION_SYNONYMS


# =========================================================
# 5. MASTER ANALYSIS ENGINE (ENGINE V2)
# =========================================================

# =========================================================
# NEW: INSIGHTS GENERATOR
# =========================================================

def generate_insights(section_scores, missing_skills, seniority, ats_score):

    insights = []

    # --- Score-based insight ---
    if ats_score < 50:
        insights.append(
            "Your resume needs stronger project depth and technical keyword coverage."
        )
    elif ats_score < 80:
        insights.append(
            "Your resume has a solid structure but could benefit from stronger industry alignment."
        )
    else:
        insights.append(
            "Your resume shows strong technical positioning and clear structure."
        )

    # --- Section health ---
    if section_scores.get("projects", 0) < 10:
        insights.append(
            "Adding detailed project descriptions can significantly improve recruiter visibility."
        )

    if section_scores.get("experience", 0) < 10:
        insights.append(
            "Use action verbs and measurable impact to strengthen your experience section."
        )

    # --- Skill gaps ---
    if missing_skills:
        insights.append(
            f"Consider adding industry tools like {', '.join(missing_skills[:2])}."
        )

    # --- Seniority context ---
    if seniority == "student":
        insights.append(
            "Focus on showcasing hands-on projects and internships to strengthen your profile."
        )

    return insights

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
    # -------- NEW SECTION SCORING --------
    section_scores = calculate_section_scores(
        clean_text,
        sections,
        found_skills,
        word_count
    )

    ats_score = calculate_resume_strength(section_scores)

    seniority_estimate = estimate_seniority(
    clean_text,
    sections,
    found_skills
    )

    insights = generate_insights(
    section_scores,
    missing_skills,
    seniority_estimate,
    ats_score
    )

    # -------- Feedback Generator --------
    feedback = {
        "strengths": [],
        "seniority_estimate": seniority_estimate,
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
        "seniority_estimate": seniority_estimate,
        "word_count": word_count,
        "details": {
            "sections_found": [s for s, ok in sections.items() if ok],
            "skills_detected": found_skills,
            "missing_core_skills": missing_skills,
            "section_scores": section_scores
        },
        "feedback": feedback,
        "insights": insights,
        "engine_version": "3.0.0"
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
            "word_count": result["word_count"],
            "section_scores": result["details"]["section_scores"],
            "seniority_estimate": result["seniority_estimate"],
            "insights": result["insights"]
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