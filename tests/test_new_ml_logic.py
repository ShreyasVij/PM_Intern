from backend.ml_model import get_recommendations
# sample candidate
candidate = {
    "skills_possessed": ["python", "data analysis", "Excel"],
    "sector_interests": ["data", "governance"],
    "location_preference": "Bengaluru",
    "field_of_study": "computer science",
    "education_level": "undergraduate",
    "first_generation": True
}
# sample internships list
internships = [
    {"internship_id": "I1", "title": "Data Intern", "organization": "OrgA",
     "location": "Bengaluru", "sector": "Data", "skills_required": ["python","sql"], "is_beginner_friendly": True},
    {"internship_id": "I2", "title": "Research Intern", "organization": "OrgB",
     "location": "Mysore", "sector": "Governance", "skills_required": ["writing","research"]},
    {"internship_id": "I3", "title": "Marketing Intern", "organization": "OrgA",
     "location": "Hyderabad", "sector": "Marketing", "skills_required": ["social media"]}
]

results = get_recommendations(candidate, internships, top_n=3)
for r in results:
    print(r["internship_id"], r["title"], r["match_score"], r["reason"])
