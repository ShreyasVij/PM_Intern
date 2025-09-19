# backend/test_education_interests.py
from db import load_data, convert_object_ids

def test_education_interests():
    """Test that education and interests fields are properly stored in MongoDB"""
    print("Testing education and interests fields in MongoDB...")
    
    # Load candidates data
    candidates = convert_object_ids(load_data("candidates"))
    
    # Find candidates with education and interests data
    candidates_with_education = []
    candidates_with_interests = []
    
    for candidate in candidates:
        if candidate.get("education_level") or candidate.get("field_of_study"):
            candidates_with_education.append(candidate)
        if candidate.get("sector_interests"):
            candidates_with_interests.append(candidate)
    
    print(f"\n📊 EDUCATION DATA:")
    print(f"✅ Candidates with education data: {len(candidates_with_education)}")
    
    for candidate in candidates_with_education[:3]:  # Show first 3 examples
        print(f"  - {candidate.get('name', 'Unknown')}:")
        print(f"    Education Level: {candidate.get('education_level', 'N/A')}")
        print(f"    Field of Study: {candidate.get('field_of_study', 'N/A')}")
        print(f"    Sector Interests: {candidate.get('sector_interests', 'N/A')}")
        print()
    
    print(f"\n📊 INTERESTS DATA:")
    print(f"✅ Candidates with interests data: {len(candidates_with_interests)}")
    
    for candidate in candidates_with_interests[:3]:  # Show first 3 examples
        print(f"  - {candidate.get('name', 'Unknown')}:")
        print(f"    Sector Interests: {candidate.get('sector_interests', 'N/A')}")
        print()
    
    # Load profiles data
    profiles = convert_object_ids(load_data("profiles"))
    
    profiles_with_education = []
    profiles_with_interests = []
    
    for profile in profiles:
        if profile.get("education_level") or profile.get("field_of_study"):
            profiles_with_education.append(profile)
        if profile.get("sector_interests"):
            profiles_with_interests.append(profile)
    
    print(f"\n📊 PROFILES DATA:")
    print(f"✅ Profiles with education data: {len(profiles_with_education)}")
    print(f"✅ Profiles with interests data: {len(profiles_with_interests)}")
    
    print("\n" + "="*60)
    print("✅ EDUCATION AND INTERESTS TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_education_interests()
