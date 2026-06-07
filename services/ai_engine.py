"""
AI Matching Engine
==================
Core module implementing:
  1. Skill vector construction (TF-IDF style, one-hot over skill vocabulary)
  2. Cosine similarity between student skill vector and internship requirement vector
  3. Weighted scoring: skill_sim * 0.50 + gpa_score * 0.25 + preference_score * 0.25
  4. Recommendation generation (top-3 per student)
  5. Greedy allocation algorithm for conflict-free slot assignment
"""

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from collections import defaultdict


# ─── Skill Vocabulary ──────────────────────────────────────────────────────────
SKILL_VOCABULARY = [
    "python", "machine learning", "sql", "javascript", "react", "node.js",
    "java", "c++", "c#", "php", "html", "css", "git", "docker", "kubernetes",
    "aws", "azure", "gcp", "linux", "networking", "cisco", "rest api",
    "graphql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib",
    "power bi", "tableau", "excel", "r", "sas", "spss", "stata",
    "data analysis", "statistics", "research", "financial analysis",
    "accounting", "auditing", "risk modeling", "bloomberg", "valuation",
    "product management", "ui/ux", "figma", "adobe xd", "agile", "scrum",
    "project management", "business analysis", "excel", "communication",
    "electrical engineering", "mechanical engineering", "chemical engineering",
    "civil engineering", "autocad", "solidworks", "matlab", "plc", "scada",
    "hysys", "process engineering", "safety management",
    "digital marketing", "seo", "social media", "google analytics",
    "content creation", "copywriting", "brand management",
    "typescript", "vue.js", "angular", "spring boot", "django", "flask",
]

SKILL_VOCAB_INDEX = {skill.lower(): idx for idx, skill in enumerate(SKILL_VOCABULARY)}
VOCAB_SIZE = len(SKILL_VOCABULARY)


# ─── Weights ───────────────────────────────────────────────────────────────────
WEIGHT_SKILL = 0.50
WEIGHT_GPA = 0.25
WEIGHT_PREFERENCE = 0.25


def build_skill_vector(skills_list: list) -> np.ndarray:
    """Convert a list of skill strings into a unit-normalized sparse vector."""
    vec = np.zeros(VOCAB_SIZE, dtype=np.float32)
    for skill in skills_list:
        idx = SKILL_VOCAB_INDEX.get(skill.lower().strip())
        if idx is not None:
            vec[idx] = 1.0
    # Add partial matches for compound skills
    for skill in skills_list:
        skill_lower = skill.lower().strip()
        for vocab_skill, idx in SKILL_VOCAB_INDEX.items():
            if skill_lower in vocab_skill or vocab_skill in skill_lower:
                vec[idx] = max(vec[idx], 0.5)
    return vec


def compute_skill_similarity(student_skills: list, required_skills: list,
                              preferred_skills: list = None) -> float:
    """
    Cosine similarity between student skill vector and internship requirement vector.
    Required skills get weight 1.0, preferred skills get weight 0.6.
    """
    student_vec = build_skill_vector(student_skills)
    intern_vec = build_skill_vector(required_skills)

    if preferred_skills:
        pref_vec = build_skill_vector(preferred_skills) * 0.6
        intern_vec = np.maximum(intern_vec, pref_vec)

    # Avoid division by zero
    if np.linalg.norm(student_vec) == 0 or np.linalg.norm(intern_vec) == 0:
        return 0.0

    sv = student_vec.reshape(1, -1)
    iv = intern_vec.reshape(1, -1)
    sim = cosine_similarity(sv, iv)[0][0]
    return float(np.clip(sim, 0.0, 1.0))


def compute_gpa_score(student_gpa: float, min_gpa: float,
                       cgpa_scale: float = 4.0) -> float:
    """
    Normalized GPA score.
    Returns 0 if below minimum, otherwise proportional within [min_gpa, scale].
    """
    if student_gpa < min_gpa:
        return 0.0
    normalized = student_gpa / cgpa_scale
    # Boost for exceeding minimum: extra credit for high GPA
    range_above_min = (student_gpa - min_gpa) / (cgpa_scale - min_gpa + 1e-6)
    return float(np.clip(0.5 * normalized + 0.5 * range_above_min, 0.0, 1.0))


def compute_preference_score(student_preferred_domains: list,
                               internship_domain: str) -> float:
    """
    Binary + fuzzy preference match.
    1.0 if exact domain match, 0.5 if partial match, 0.0 otherwise.
    """
    if not student_preferred_domains or not internship_domain:
        return 0.5  # neutral if no preference given

    domain_lower = internship_domain.lower()
    for pref in student_preferred_domains:
        pref_lower = pref.lower()
        if pref_lower == domain_lower:
            return 1.0
        if pref_lower in domain_lower or domain_lower in pref_lower:
            return 0.7
    return 0.0


def compute_final_score(skill_sim: float, gpa_score: float,
                         pref_score: float) -> float:
    """Weighted composite score."""
    score = (WEIGHT_SKILL * skill_sim +
             WEIGHT_GPA * gpa_score +
             WEIGHT_PREFERENCE * pref_score)
    return round(float(np.clip(score, 0.0, 1.0)), 4)


# ─── Batch Matching ────────────────────────────────────────────────────────────

def run_matching_engine(students: list, internships: list) -> list:
    """
    Compute match scores for all student × internship pairs.

    Args:
        students: list of dicts with keys: id, gpa, cgpa_scale, skills (JSON str),
                  preferred_domains (JSON str)
        internships: list of dicts with keys: id, required_skills (JSON str),
                     preferred_skills (JSON str), domain, min_gpa, is_active

    Returns:
        List of dicts: {student_id, internship_id, skill_similarity,
                        gpa_score, preference_score, final_score}
    """
    results = []

    for student in students:
        try:
            s_skills = json.loads(student.get('skills') or '[]')
            s_prefs = json.loads(student.get('preferred_domains') or '[]')
            s_gpa = float(student.get('gpa') or 0)
            s_scale = float(student.get('cgpa_scale') or 4.0)
        except (json.JSONDecodeError, TypeError):
            s_skills, s_prefs, s_gpa, s_scale = [], [], 0.0, 4.0

        for intern in internships:
            if not intern.get('is_active', True):
                continue
            try:
                req_skills = json.loads(intern.get('required_skills') or '[]')
                pref_skills = json.loads(intern.get('preferred_skills') or '[]')
                min_gpa = float(intern.get('min_gpa') or 0)
                domain = intern.get('domain') or ''
            except (json.JSONDecodeError, TypeError):
                req_skills, pref_skills, min_gpa, domain = [], [], 0.0, ''

            skill_sim = compute_skill_similarity(s_skills, req_skills, pref_skills)
            gpa_score = compute_gpa_score(s_gpa, min_gpa, s_scale)
            pref_score = compute_preference_score(s_prefs, domain)
            final = compute_final_score(skill_sim, gpa_score, pref_score)

            results.append({
                'student_id': student['id'],
                'internship_id': intern['id'],
                'skill_similarity': round(skill_sim, 4),
                'gpa_score': round(gpa_score, 4),
                'preference_score': round(pref_score, 4),
                'final_score': final
            })

    return results


# ─── Recommendation Engine ─────────────────────────────────────────────────────

def generate_recommendations(match_scores: list, top_n: int = 3) -> dict:
    """
    For each student, select top-N internships by final_score.

    Returns:
        dict mapping student_id -> list of {internship_id, rank, score}
    """
    by_student = defaultdict(list)
    for row in match_scores:
        by_student[row['student_id']].append(row)

    recommendations = {}
    for student_id, scores in by_student.items():
        top = sorted(scores, key=lambda x: x['final_score'], reverse=True)[:top_n]
        recommendations[student_id] = [
            {
                'internship_id': s['internship_id'],
                'rank': i + 1,
                'final_score': s['final_score'],
                'skill_similarity': s['skill_similarity'],
                'gpa_score': s['gpa_score'],
                'preference_score': s['preference_score']
            }
            for i, s in enumerate(top)
        ]

    return recommendations


# ─── Greedy Allocation Algorithm ───────────────────────────────────────────────

def greedy_allocation(match_scores: list, internship_slots: dict,
                       student_choices: dict = None) -> dict:
    """
    Greedy assignment: assign each student to their highest-scoring internship
    with available slots. Students are processed in descending order of their
    best available match score (ensures best-fit students get priority).

    Args:
        match_scores: list of match score dicts (from run_matching_engine)
        internship_slots: dict {internship_id: available_slots}
        student_choices: optional dict {student_id: preferred_internship_id}
                         (if student accepted a recommendation)

    Returns:
        dict {student_id: {internship_id, score, method}}
    """
    # Build per-student ranked lists
    by_student = defaultdict(list)
    for row in match_scores:
        by_student[row['student_id']].append(row)

    for sid in by_student:
        by_student[sid].sort(key=lambda x: x['final_score'], reverse=True)

    # Sort students by their best score (priority ordering)
    student_priority = sorted(
        by_student.keys(),
        key=lambda sid: by_student[sid][0]['final_score'] if by_student[sid] else 0,
        reverse=True
    )

    remaining_slots = dict(internship_slots)
    allocations = {}

    # First pass: honour student choices (accepted recommendations)
    if student_choices:
        for student_id, chosen_internship_id in student_choices.items():
            if (remaining_slots.get(chosen_internship_id, 0) > 0 and
                    student_id not in allocations):
                score = next(
                    (r['final_score'] for r in by_student[student_id]
                     if r['internship_id'] == chosen_internship_id), 0
                )
                allocations[student_id] = {
                    'internship_id': chosen_internship_id,
                    'score': score,
                    'method': 'student_choice'
                }
                remaining_slots[chosen_internship_id] -= 1

    # Second pass: greedy best-fit for remaining students
    for student_id in student_priority:
        if student_id in allocations:
            continue

        for candidate in by_student[student_id]:
            iid = candidate['internship_id']
            if remaining_slots.get(iid, 0) > 0:
                allocations[student_id] = {
                    'internship_id': iid,
                    'score': candidate['final_score'],
                    'method': 'ai_recommended'
                }
                remaining_slots[iid] -= 1
                break

    return allocations


# ─── Score explanation helper ──────────────────────────────────────────────────

def explain_match(student_skills: list, required_skills: list,
                   preferred_skills: list, student_preferred_domains: list,
                   internship_domain: str, student_gpa: float,
                   min_gpa: float) -> dict:
    """Return a human-readable breakdown of match components."""
    matched = [s for s in student_skills
               if s.lower() in [r.lower() for r in required_skills]]
    missing = [r for r in required_skills
               if r.lower() not in [s.lower() for s in student_skills]]
    bonus = [s for s in student_skills
             if s.lower() in [p.lower() for p in (preferred_skills or [])]]

    skill_sim = compute_skill_similarity(student_skills, required_skills, preferred_skills)
    gpa_score = compute_gpa_score(student_gpa, min_gpa)
    pref_score = compute_preference_score(student_preferred_domains, internship_domain)
    final = compute_final_score(skill_sim, gpa_score, pref_score)

    return {
        'final_score': final,
        'skill_similarity': round(skill_sim, 4),
        'gpa_score': round(gpa_score, 4),
        'preference_score': round(pref_score, 4),
        'matched_skills': matched,
        'missing_skills': missing,
        'bonus_skills': bonus,
        'gpa_eligible': student_gpa >= min_gpa,
        'domain_match': pref_score > 0,
        'weights': {
            'skill': WEIGHT_SKILL,
            'gpa': WEIGHT_GPA,
            'preference': WEIGHT_PREFERENCE
        }
    }