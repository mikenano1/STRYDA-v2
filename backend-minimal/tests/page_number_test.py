#!/usr/bin/env python3
"""
Page Number Preservation Test
Tests that 3-digit page numbers like 184 are not truncated to 18
"""

import requests
import json
import sys

API_BASE = "http://localhost:8001"


def test_page_number_preservation():
    """
    Test that page numbers are not truncated in citations
    """
    print("Testing page number preservation in citation pills...\n")
    
    # Check backend health
    try:
        health = requests.get(f"{API_BASE}/health", timeout=5).json()
        print(f"✅ Backend healthy: v{health['version']}\n")
    except Exception as e:
        print(f"❌ Backend not available: {e}")
        return False
    
    # Test queries that should return various page numbers
    test_cases = [
        {
            "query": "minimum apron flashing cover per E2/AS1",
            "expected_pages": [7, 11, 18],  # Should NOT be truncated
            "description": "E2/AS1 apron flashing query"
        },
        {
            "query": "NZS 3604 stud spacing",
            "description": "NZS 3604 query"
        },
        {
            "query": "B1 Amendment 13 bracing",
            "description": "B1 Amendment 13 query"
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        query = test["query"]
        description = test["description"]
        
        print(f"Test: {description}")
        print(f"Query: {query}")
        
        try:
            response = requests.post(
                f"{API_BASE}/api/chat",
                json={"message": query, "session_id": "page-test"},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}")
                all_passed = False
                continue
            
            data = response.json()
            citations = data.get("citations", [])
            
            if not citations:
                print(f"  ⚠️ No citations returned")
                continue
            
            # Check each citation's page number
            for cite in citations:
                source = cite.get("source", "Unknown")
                page = cite.get("page", 0)
                pill_text = cite.get("pill_text", "")
                
                # Verify page number consistency
                if f"p.{page}" not in pill_text:
                    print(f"  ❌ TRUNCATION BUG: {source} page {page} not in pill_text '{pill_text}'")
                    all_passed = False
                else:
                    # Check for common truncation patterns
                    if page >= 100:
                        # For 3-digit pages, ensure all digits present
                        page_str = str(page)
                        if not page_str in pill_text:
                            print(f"  ❌ TRUNCATION: {source} p.{page} truncated in '{pill_text}'")
                            all_passed = False
                        else:
                            print(f"  ✅ {source} p.{page} - Full page number preserved")
                    else:
                        print(f"  ✅ {source} p.{page}")
            
            # Check expected pages if specified
            if "expected_pages" in test:
                actual_pages = [c["page"] for c in citations]
                for expected_page in test["expected_pages"]:
                    if expected_page not in actual_pages:
                        print(f"  ⚠️ Expected page {expected_page} not in results {actual_pages}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            all_passed = False
    
    return all_passed


def test_page_extraction_module():
    """
    Test the locator.py module directly
    """
    print("\n" + "="*80)
    print("Testing services/citations/locator.py module...")
    print("="*80 + "\n")
    
    try:
        import sys
        sys.path.insert(0, "/app/backend-minimal")
        from services.citations.locator import extract_page_number, normalize_page_reference
        
        test_cases = [
            ("E2/AS1 p.184", 184),
            ("page 184", 184),
            ("p. 184", 184),
            ("p.7", 7),
            ("p.11", 11),
            ("p.18", 18),
            ("NZS 3604 p.45", 45),
            ("B1/AS1 p.8", 8),
        ]
        
        all_passed = True
        for text, expected in test_cases:
            actual = extract_page_number(text)
            normalized = normalize_page_reference(expected)
            
            if actual != expected:
                print(f"  ❌ extract_page_number('{text}') = {actual}, expected {expected}")
                all_passed = False
            elif normalized != f"p.{expected}":
                print(f"  ❌ normalize_page_reference({expected}) = {normalized}, expected p.{expected}")
                all_passed = False
            else:
                print(f"  ✅ '{text}' → {actual} → {normalized}")
        
        if all_passed:
            print("\n✅ All locator module tests passed!")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Module test failed: {e}")
        return False


def main():
    """Main entry point"""
    print("="*80)
    print("PAGE NUMBER PRESERVATION TEST SUITE")
    print("="*80 + "\n")
    
    # Test 1: Module-level tests
    module_ok = test_page_extraction_module()
    
    # Test 2: Integration tests
    integration_ok = test_page_number_preservation()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Module Tests: {'✅ PASSED' if module_ok else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_ok else '❌ FAILED'}")
    
    if module_ok and integration_ok:
        print("\n✅ ALL TESTS PASSED - Page numbers preserved correctly!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
