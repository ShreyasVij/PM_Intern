#!/usr/bin/env python3
"""
Quick test script to debug API endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:3000"

def test_endpoint(endpoint, description):
    """Test an API endpoint and print results"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTesting: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Success - Data type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"List length: {len(data)}")
            except:
                print(f"Success - Text response: {response.text[:100]}...")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")

def main():
    """Test all main endpoints"""
    print("Testing PM Intern API Endpoints")
    
    # Test basic endpoints
    test_endpoint("/", "Home endpoint")
    test_endpoint("/health", "Health check")
    test_endpoint("/frontend/pages/index.html", "Frontend static file")
    
    # Test API endpoints
    test_endpoint("/api/internships", "Internships API")
    test_endpoint("/api/recommendations/test123", "Recommendations (non-existent user)")
    test_endpoint("/api/recommendations/by_internship/123", "Recommendations by internship")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()