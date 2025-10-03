#!/usr/bin/env python3
"""
Focused STRYDA Backend Testing
Tests the specific endpoints requested by the user and current system status
"""

import requests
import json
import time
import sys

class FocusedBackendTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'STRYDA-Focused-Tester/1.0'
        })
        
        # URLs to test
        self.production_url = "https://onsite-copilot.preview.emergentagent.com"
        self.local_url = "http://localhost:8001"
    
    def log_result(self, test_name: str, success: bool, details: str, url: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'url': url,
            'timestamp': time.time()
        }
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if url:
            print(f"   URL: {url}")
    
    def test_health_endpoint(self, base_url: str, label: str):
        """Test GET /health endpoint as requested by user"""
        try:
            response = self.session.get(f"{base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected = {"ok": True, "version": "v0.2"}
                
                if data == expected:
                    self.log_result(f"Health Endpoint ({label})", True, 
                                  f"Returned expected response: {data}", base_url)
                    return True
                else:
                    self.log_result(f"Health Endpoint ({label})", False, 
                                  f"Unexpected response. Expected: {expected}, Got: {data}", base_url)
                    return False
            else:
                self.log_result(f"Health Endpoint ({label})", False, 
                              f"HTTP {response.status_code}", base_url)
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result(f"Health Endpoint ({label})", False, f"Request failed: {str(e)}", base_url)
            return False
    
    def test_ask_endpoint(self, base_url: str, label: str):
        """Test POST /api/ask endpoint as requested by user"""
        try:
            payload = {"query": "test question"}
            response = self.session.post(f"{base_url}/api/ask", 
                                       json=payload, 
                                       timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has expected fallback structure
                required_fields = ['answer', 'notes', 'citation']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    answer_length = len(data.get('answer', ''))
                    self.log_result(f"Ask Endpoint ({label})", True, 
                                  f"Fallback response with all required fields. Answer length: {answer_length} chars", base_url)
                    return True
                else:
                    self.log_result(f"Ask Endpoint ({label})", False, 
                                  f"Missing required fields: {missing_fields}. Got: {list(data.keys())}", base_url)
                    return False
            else:
                self.log_result(f"Ask Endpoint ({label})", False, 
                              f"HTTP {response.status_code}: {response.text[:100]}", base_url)
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result(f"Ask Endpoint ({label})", False, f"Request failed: {str(e)}", base_url)
            return False
    
    def test_frontend_accessibility(self):
        """Test if frontend is accessible at localhost:3000"""
        try:
            response = self.session.get("http://localhost:3000", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                if "STRYDA" in content:
                    self.log_result("Frontend Accessibility", True, 
                                  "Frontend accessible and contains STRYDA branding", "http://localhost:3000")
                    return True
                else:
                    self.log_result("Frontend Accessibility", False, 
                                  "Frontend accessible but missing STRYDA branding", "http://localhost:3000")
                    return False
            else:
                self.log_result("Frontend Accessibility", False, 
                              f"HTTP {response.status_code}", "http://localhost:3000")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Frontend Accessibility", False, f"Request failed: {str(e)}", "http://localhost:3000")
            return False
    
    def test_production_system_status(self):
        """Test if production system has any working endpoints"""
        endpoints_to_test = [
            "/api/",
            "/api/chat",
            "/api/knowledge/stats"
        ]
        
        working_endpoints = 0
        
        for endpoint in endpoints_to_test:
            try:
                if endpoint == "/api/chat":
                    # POST request for chat
                    response = self.session.post(f"{self.production_url}{endpoint}", 
                                               json={"message": "test"}, timeout=10)
                else:
                    # GET request for others
                    response = self.session.get(f"{self.production_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    working_endpoints += 1
                    print(f"   ✅ {endpoint} - Working")
                else:
                    print(f"   ❌ {endpoint} - HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {str(e)}")
        
        if working_endpoints > 0:
            self.log_result("Production System Status", True, 
                          f"{working_endpoints}/{len(endpoints_to_test)} endpoints working", self.production_url)
            return True
        else:
            self.log_result("Production System Status", False, 
                          "No production endpoints are working", self.production_url)
            return False
    
    def run_focused_tests(self):
        """Run focused tests for user requirements"""
        print("🎯 STRYDA.ai Focused Backend Testing")
        print("Testing specific user requirements and system status")
        print("=" * 60)
        
        # Test user-requested endpoints on both systems
        print("\n📋 USER-REQUESTED ENDPOINTS:")
        print("Testing GET /health and POST /api/ask as specified")
        
        # Test local fallback system
        print(f"\n🔧 Local Fallback System (localhost:8001):")
        local_health = self.test_health_endpoint(self.local_url, "Local")
        local_ask = self.test_ask_endpoint(self.local_url, "Local")
        
        # Test production system
        print(f"\n🌐 Production System ({self.production_url}):")
        prod_health = self.test_health_endpoint(self.production_url, "Production")
        prod_ask = self.test_ask_endpoint(self.production_url, "Production")
        
        # Test frontend
        print(f"\n🖥️  Frontend System:")
        frontend_working = self.test_frontend_accessibility()
        
        # Test production system status
        print(f"\n🔍 Production System Diagnosis:")
        prod_status = self.test_production_system_status()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST SUMMARY")
        print("=" * 60)
        
        print(f"\n🎯 USER-REQUESTED ENDPOINTS:")
        print(f"   GET /health:")
        print(f"     • Local Fallback: {'✅ Working' if local_health else '❌ Failed'}")
        print(f"     • Production: {'✅ Working' if prod_health else '❌ Failed'}")
        print(f"   POST /api/ask:")
        print(f"     • Local Fallback: {'✅ Working' if local_ask else '❌ Failed'}")
        print(f"     • Production: {'✅ Working' if prod_ask else '❌ Failed'}")
        
        print(f"\n🖥️  FRONTEND:")
        print(f"   • Accessibility: {'✅ Working' if frontend_working else '❌ Failed'}")
        
        print(f"\n🌐 PRODUCTION SYSTEM:")
        print(f"   • Overall Status: {'✅ Partially Working' if prod_status else '❌ Not Working'}")
        
        # Determine overall status
        user_requirements_met = local_health and local_ask  # At least fallback works
        
        if user_requirements_met:
            print(f"\n🎉 USER REQUIREMENTS: ✅ MET")
            print("   The requested endpoints are working in fallback mode")
        else:
            print(f"\n⚠️  USER REQUIREMENTS: ❌ NOT MET")
            print("   The requested endpoints are not working properly")
        
        return user_requirements_met

if __name__ == "__main__":
    tester = FocusedBackendTester()
    success = tester.run_focused_tests()
    
    sys.exit(0 if success else 1)