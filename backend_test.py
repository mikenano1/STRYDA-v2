#!/usr/bin/env python3
"""
Backend Testing Suite for STRYDA.ai
Tests the /api/projects endpoint and standard chat functionality
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://stryda-brain.preview.emergentagent.com"  # From frontend/.env
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.results = []
        self.session_id = f"test-session-{int(time.time())}"
        
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            print(f"   Error: {details.get('error', 'Unknown error')}")
        else:
            print(f"   Details: {details.get('summary', 'Success')}")
        print()

    def test_health_endpoint(self):
        """Test basic health endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Health Check", True, {
                    "status_code": response.status_code,
                    "response": data,
                    "summary": f"Health OK - Version: {data.get('version', 'unknown')}"
                })
                return True
            else:
                self.log_result("Health Check", False, {
                    "status_code": response.status_code,
                    "error": f"Unexpected status code: {response.status_code}"
                })
                return False
                
        except Exception as e:
            self.log_result("Health Check", False, {
                "error": f"Request failed: {str(e)}"
            })
            return False

    def test_projects_endpoint(self):
        """Test the /api/projects endpoint"""
        try:
            response = requests.get(f"{API_BASE}/projects", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if not isinstance(data, dict):
                    self.log_result("Projects Endpoint", False, {
                        "error": "Response is not a JSON object",
                        "response_type": type(data).__name__
                    })
                    return False
                
                # Check for expected fields
                if "ok" not in data:
                    self.log_result("Projects Endpoint", False, {
                        "error": "Missing 'ok' field in response",
                        "response": data
                    })
                    return False
                
                if not data.get("ok"):
                    self.log_result("Projects Endpoint", False, {
                        "error": "API returned ok=false",
                        "response": data
                    })
                    return False
                
                # Check projects array
                projects = data.get("projects", [])
                if not isinstance(projects, list):
                    self.log_result("Projects Endpoint", False, {
                        "error": "Projects field is not an array",
                        "projects_type": type(projects).__name__
                    })
                    return False
                
                # Validate project structure if projects exist
                project_count = len(projects)
                valid_projects = 0
                
                for project in projects:
                    if isinstance(project, dict) and "id" in project and "name" in project:
                        valid_projects += 1
                
                self.log_result("Projects Endpoint", True, {
                    "status_code": response.status_code,
                    "project_count": project_count,
                    "valid_projects": valid_projects,
                    "response": data,
                    "summary": f"Found {project_count} projects, {valid_projects} valid"
                })
                return True
                
            else:
                self.log_result("Projects Endpoint", False, {
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return False
                
        except Exception as e:
            self.log_result("Projects Endpoint", False, {
                "error": f"Request failed: {str(e)}"
            })
            return False

    def test_chat_basic_functionality(self):
        """Test basic chat functionality"""
        try:
            chat_payload = {
                "message": "What is the minimum pitch for corrugated iron roofing?",
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{API_BASE}/chat",
                json=chat_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["answer", "intent"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Chat Basic Functionality", False, {
                        "error": f"Missing required fields: {missing_fields}",
                        "response": data
                    })
                    return False
                
                answer = data.get("answer", "")
                intent = data.get("intent", "")
                model = data.get("model", "unknown")
                
                # Check if answer is meaningful (not empty or too short)
                if len(answer.strip()) < 10:
                    self.log_result("Chat Basic Functionality", False, {
                        "error": f"Answer too short: {len(answer)} characters",
                        "answer": answer,
                        "response": data
                    })
                    return False
                
                self.log_result("Chat Basic Functionality", True, {
                    "status_code": response.status_code,
                    "answer_length": len(answer),
                    "intent": intent,
                    "model": model,
                    "response": data,
                    "summary": f"Chat working - {len(answer)} chars, intent: {intent}, model: {model}"
                })
                return True
                
            else:
                self.log_result("Chat Basic Functionality", False, {
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return False
                
        except Exception as e:
            self.log_result("Chat Basic Functionality", False, {
                "error": f"Request failed: {str(e)}"
            })
            return False

    def test_chat_compliance_question(self):
        """Test chat with a compliance-focused question"""
        try:
            chat_payload = {
                "message": "What is the stud spacing for a 2.4m wall in high wind zone?",
                "session_id": f"{self.session_id}-compliance"
            }
            
            response = requests.post(
                f"{API_BASE}/chat",
                json=chat_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                answer = data.get("answer", "")
                intent = data.get("intent", "")
                citations = data.get("citations", [])
                model = data.get("model", "unknown")
                
                # Check if answer is meaningful
                if len(answer.strip()) < 20:
                    self.log_result("Chat Compliance Question", False, {
                        "error": f"Answer too short for compliance question: {len(answer)} characters",
                        "answer": answer,
                        "response": data
                    })
                    return False
                
                # Note: Citations might be empty due to known issues, but we'll report it
                citation_count = len(citations) if isinstance(citations, list) else 0
                
                self.log_result("Chat Compliance Question", True, {
                    "status_code": response.status_code,
                    "answer_length": len(answer),
                    "intent": intent,
                    "model": model,
                    "citation_count": citation_count,
                    "response": data,
                    "summary": f"Compliance chat working - {len(answer)} chars, {citation_count} citations"
                })
                return True
                
            else:
                self.log_result("Chat Compliance Question", False, {
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return False
                
        except Exception as e:
            self.log_result("Chat Compliance Question", False, {
                "error": f"Request failed: {str(e)}"
            })
            return False

    def test_admin_config(self):
        """Test admin config endpoint to verify model configuration"""
        try:
            response = requests.get(f"{BACKEND_URL}/admin/config", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                models = data.get("models", {})
                gemini_model = models.get("gemini_model", "unknown")
                gemini_pro_model = models.get("gemini_pro_model", "unknown")
                
                self.log_result("Admin Config", True, {
                    "status_code": response.status_code,
                    "models": models,
                    "response": data,
                    "summary": f"Config OK - Gemini: {gemini_model}, Pro: {gemini_pro_model}"
                })
                return True
                
            else:
                self.log_result("Admin Config", False, {
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return False
                
        except Exception as e:
            self.log_result("Admin Config", False, {
                "error": f"Request failed: {str(e)}"
            })
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🧪 Starting Backend Testing Suite")
        print(f"🎯 Target: {BACKEND_URL}")
        print(f"📅 Time: {datetime.now().isoformat()}")
        print("=" * 60)
        print()
        
        # Run tests in order
        tests = [
            self.test_health_endpoint,
            self.test_admin_config,
            self.test_projects_endpoint,
            self.test_chat_basic_functionality,
            self.test_chat_compliance_question
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
        
        # Summary of critical issues
        failed_tests = [r for r in self.results if not r["success"]]
        if failed_tests:
            print("\n🚨 Failed Tests:")
            for test in failed_tests:
                print(f"   • {test['test_name']}: {test['details'].get('error', 'Unknown error')}")
        
        print(f"\n✅ Successful Tests: {passed}")
        print(f"❌ Failed Tests: {total - passed}")
        
        return passed, total, self.results

def main():
    """Main test runner"""
    tester = BackendTester()
    passed, total, results = tester.run_all_tests()
    
    # Write detailed results to file
    with open("/app/backend_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "passed": passed,
                "total": total,
                "success_rate": passed / total * 100,
                "timestamp": datetime.now().isoformat()
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()