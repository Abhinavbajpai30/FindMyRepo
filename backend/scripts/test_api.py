#!/usr/bin/env python3
"""
Test script for FindMyRepo API endpoints
Run this after starting the server to verify all endpoints work correctly
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """Test the health check endpoint"""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search():
    """Test the search endpoint"""
    print_section("Testing Search Endpoint")
    
    test_queries = [
        "python web framework",
        "machine learning pytorch",
        "javascript react components"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        try:
            response = requests.post(
                f"{BASE_URL}/search",
                json={"query": query},
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success')}")
                print(f"Results count: {len(data.get('results', []))}")
                
                if data.get('results'):
                    first_result = data['results'][0]
                    print(f"Top result: {first_result.get('name')} ({first_result.get('stars')} stars)")
                    print(f"Languages: {', '.join(first_result.get('languages', []))}")
                
                print("✅ Search test passed")
            else:
                print(f"❌ Search failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_user_preferences():
    """Test the user preferences endpoint"""
    print_section("Testing User Preferences Endpoint")
    
    preferences = {
        "primaryDomains": ["Backend / APIs", "ML / AI / Data Science"],
        "role": "Software Developer / Engineer",
        "expertise": "Medium",
        "preferredLanguages": ["Python", "JavaScript"]
    }
    
    print(f"Preferences: {json.dumps(preferences, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/userpreferences",
            json=preferences,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Results count: {len(data.get('results', []))}")
            
            if data.get('results'):
                print("\nTop 3 recommendations:")
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"  {i}. {result.get('name')} - {result.get('description', '')[:60]}...")
                    print(f"     Stars: {result.get('stars')}, Languages: {', '.join(result.get('languages', [])[:3])}")
            
            print("✅ User preferences test passed")
        else:
            print(f"❌ User preferences failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_all_repos():
    """Test the all repos endpoint with various filters"""
    print_section("Testing All Repos Endpoint")
    
    test_cases = [
        {
            "name": "Basic pagination",
            "params": {"page": 1, "limit": 5, "sort_by": "stars", "sort_order": "desc"}
        },
        {
            "name": "Filter by language",
            "params": {"page": 1, "limit": 5, "languages": "Python,JavaScript", "sort_by": "stars", "sort_order": "desc"}
        },
        {
            "name": "Filter by star range",
            "params": {"page": 1, "limit": 5, "min_stars": 1000, "max_stars": 10000, "sort_by": "stars", "sort_order": "desc"}
        },
        {
            "name": "Search by name",
            "params": {"page": 1, "limit": 5, "name_contains": "react", "sort_by": "stars", "sort_order": "desc"}
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Params: {test_case['params']}")
        
        try:
            response = requests.get(f"{BASE_URL}/allrepos", params=test_case['params'])
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success')}")
                print(f"Results: {len(data.get('data', []))}")
                
                pagination = data.get('pagination', {})
                print(f"Total items: {pagination.get('total_items')}")
                print(f"Total pages: {pagination.get('total_pages')}")
                print(f"Current page: {pagination.get('current_page')}")
                
                if data.get('data'):
                    first_result = data['data'][0]
                    print(f"First result: {first_result.get('name')} ({first_result.get('stars')} stars)")
                
                print("✅ Test passed")
            else:
                print(f"❌ Test failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_hidden_gems():
    """Test the hidden gems endpoint"""
    print_section("Testing Hidden Gems Endpoint")
    
    params = {"page": 1, "limit": 10, "sort_by": "stars", "sort_order": "desc"}
    
    try:
        response = requests.get(f"{BASE_URL}/hiddengem", params=params)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Results: {len(data.get('data', []))}")
            
            pagination = data.get('pagination', {})
            print(f"Total hidden gems: {pagination.get('total_items')}")
            
            if data.get('data'):
                print("\nSome hidden gems:")
                for i, result in enumerate(data['data'][:5], 1):
                    print(f"  {i}. {result.get('name')} ({result.get('stars')} ⭐)")
                    print(f"     {result.get('description', '')[:70]}...")
            
            print("✅ Hidden gems test passed")
        else:
            print(f"❌ Hidden gems test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🧪 FindMyRepo API Test Suite")
    print(f"Testing server at: {BASE_URL}")
    
    # Test connection first
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print(f"❌ Cannot connect to server at {BASE_URL}")
            print("Make sure the server is running: python main.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Make sure the server is running: python main.py")
        sys.exit(1)
    
    # Run all tests
    test_health_check()
    test_search()
    test_user_preferences()
    test_all_repos()
    test_hidden_gems()
    
    print("\n" + "="*60)
    print("  All tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()