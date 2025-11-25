#!/usr/bin/env python3
"""
STRYDA.ai Vision AI Backend Testing Suite
Tests the Vision AI integration with GPT-4O for technical diagram analysis
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import tempfile

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('EXPO_PUBLIC_BACKEND_URL', 'https://codequery-4.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class VisionAITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.session_id = str(uuid.uuid4())
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def create_test_construction_diagram(self):
        """Create a test construction diagram image"""
        try:
            # Create a simple construction diagram
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw a simple house cross-section with building elements
            # Foundation
            draw.rectangle([100, 500, 700, 550], fill='gray', outline='black', width=2)
            draw.text((400, 520), "CONCRETE FOUNDATION", fill='black', anchor='mm')
            
            # Walls
            draw.rectangle([100, 200, 150, 500], fill='lightblue', outline='black', width=2)
            draw.rectangle([650, 200, 700, 500], fill='lightblue', outline='black', width=2)
            draw.text((75, 350), "EXTERNAL\nWALL", fill='black', anchor='mm')
            
            # Roof structure
            draw.polygon([(100, 200), (400, 100), (700, 200)], fill='brown', outline='black', width=2)
            draw.text((400, 150), "ROOF STRUCTURE", fill='white', anchor='mm')
            
            # Fireplace and hearth
            draw.rectangle([300, 400, 500, 500], fill='red', outline='black', width=2)
            draw.rectangle([250, 480, 550, 500], fill='darkgray', outline='black', width=2)
            draw.text((400, 450), "FIREPLACE", fill='white', anchor='mm')
            draw.text((400, 490), "HEARTH - 300mm CLEARANCE", fill='white', anchor='mm')
            
            # Insulation
            draw.rectangle([150, 200, 180, 500], fill='yellow', outline='black', width=1)
            draw.text((165, 350), "R2.2\nINSULATION", fill='black', anchor='mm')
            
            # Labels and dimensions
            draw.text((400, 50), "NZ BUILDING CODE COMPLIANCE DIAGRAM", fill='black', anchor='mm')
            draw.text((400, 580), "H1 ENERGY EFFICIENCY | E2 WEATHERTIGHTNESS | G5 FIRE SAFETY", fill='black', anchor='mm')
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name, 'PNG')
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            print(f"Error creating test diagram: {e}")
            return None
    
    def create_invalid_file(self):
        """Create an invalid file for error testing"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w')
            temp_file.write("This is not an image file")
            temp_file.close()
            return temp_file.name
        except Exception as e:
            print(f"Error creating invalid file: {e}")
            return None
    
    def create_large_image(self):
        """Create a large image for size testing"""
        try:
            # Create a 10MB+ image
            img = Image.new('RGB', (4000, 3000), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((2000, 1500), "LARGE TEST IMAGE", fill='black', anchor='mm')
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_file.name, 'PNG')
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            print(f"Error creating large image: {e}")
            return None
    
    def test_vision_endpoint_basic(self):
        """Test basic Vision AI endpoint functionality"""
        try:
            # Create test construction diagram
            test_image_path = self.create_test_construction_diagram()
            if not test_image_path:
                self.log_test("Vision Endpoint Basic", False, "Failed to create test image")
                return False
            
            # Test with construction diagram
            with open(test_image_path, 'rb') as img_file:
                files = {'file': ('construction_diagram.png', img_file, 'image/png')}
                data = {
                    'message': 'Analyze this construction diagram for NZ Building Code compliance',
                    'session_id': self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat/vision", files=files, data=data)
                
                if response.status_code == 200:
                    vision_response = response.json()
                    ai_response = vision_response.get('response', '')
                    processing_time = vision_response.get('processing_time_ms', 0)
                    model_used = vision_response.get('model_used', '')
                    image_analyzed = vision_response.get('image_analyzed', False)
                    
                    # Check response quality
                    response_lower = ai_response.lower()
                    has_nz_context = any(term in response_lower for term in ['new zealand', 'nz', 'building code', 'compliance'])
                    has_technical_analysis = any(term in response_lower for term in ['diagram', 'construction', 'fireplace', 'insulation', 'hearth'])
                    is_substantial = len(ai_response) > 200
                    
                    if ai_response and has_nz_context and has_technical_analysis and is_substantial and image_analyzed:
                        details = {
                            "response_length": len(ai_response),
                            "processing_time_ms": processing_time,
                            "model_used": model_used,
                            "has_nz_context": has_nz_context,
                            "has_technical_analysis": has_technical_analysis
                        }
                        self.log_test("Vision Endpoint Basic", True, f"Vision AI analyzed construction diagram successfully", details)
                        
                        # Clean up
                        os.unlink(test_image_path)
                        return True
                    else:
                        issues = []
                        if not ai_response:
                            issues.append("No AI response")
                        if not has_nz_context:
                            issues.append("Missing NZ building context")
                        if not has_technical_analysis:
                            issues.append("Missing technical analysis")
                        if not is_substantial:
                            issues.append("Response too short")
                        if not image_analyzed:
                            issues.append("Image not analyzed")
                        
                        self.log_test("Vision Endpoint Basic", False, f"Issues: {', '.join(issues)}", {
                            "response": ai_response[:300] + "..." if len(ai_response) > 300 else ai_response,
                            "processing_time": processing_time,
                            "model_used": model_used
                        })
                        os.unlink(test_image_path)
                        return False
                else:
                    self.log_test("Vision Endpoint Basic", False, f"HTTP {response.status_code}", response.text)
                    os.unlink(test_image_path)
                    return False
                    
        except Exception as e:
            self.log_test("Vision Endpoint Basic", False, f"Error: {str(e)}")
            return False
    
    def test_gpt4o_integration(self):
        """Test GPT-4O model integration specifically"""
        try:
            test_image_path = self.create_test_construction_diagram()
            if not test_image_path:
                self.log_test("GPT-4O Integration", False, "Failed to create test image")
                return False
            
            with open(test_image_path, 'rb') as img_file:
                files = {'file': ('technical_diagram.png', img_file, 'image/png')}
                data = {
                    'message': 'What specific NZ Building Code clauses apply to this construction detail?',
                    'session_id': self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat/vision", files=files, data=data)
                
                if response.status_code == 200:
                    vision_response = response.json()
                    model_used = vision_response.get('model_used', '')
                    ai_response = vision_response.get('response', '')
                    
                    # Verify GPT-4O is being used
                    if model_used == 'gpt-4o':
                        # Check for advanced vision analysis capabilities
                        response_lower = ai_response.lower()
                        has_code_references = any(code in response_lower for code in ['g5', 'h1', 'e2', 'clause', 'nzbc'])
                        has_detailed_analysis = len(ai_response) > 300
                        has_building_terminology = any(term in response_lower for term in ['hearth', 'clearance', 'insulation', 'weathertight'])
                        
                        if has_code_references and has_detailed_analysis and has_building_terminology:
                            self.log_test("GPT-4O Integration", True, f"GPT-4O providing detailed NZ building analysis", {
                                "model_confirmed": model_used,
                                "response_length": len(ai_response),
                                "has_code_references": has_code_references
                            })
                            os.unlink(test_image_path)
                            return True
                        else:
                            self.log_test("GPT-4O Integration", False, "GPT-4O response lacks expected detail", {
                                "model_used": model_used,
                                "response_preview": ai_response[:200]
                            })
                            os.unlink(test_image_path)
                            return False
                    else:
                        self.log_test("GPT-4O Integration", False, f"Expected gpt-4o, got {model_used}")
                        os.unlink(test_image_path)
                        return False
                else:
                    self.log_test("GPT-4O Integration", False, f"HTTP {response.status_code}", response.text)
                    os.unlink(test_image_path)
                    return False
                    
        except Exception as e:
            self.log_test("GPT-4O Integration", False, f"Error: {str(e)}")
            return False
    
    def test_nz_building_terminology(self):
        """Test that responses include proper NZ building terminology"""
        try:
            test_image_path = self.create_test_construction_diagram()
            if not test_image_path:
                self.log_test("NZ Building Terminology", False, "Failed to create test image")
                return False
            
            with open(test_image_path, 'rb') as img_file:
                files = {'file': ('nz_construction.png', img_file, 'image/png')}
                data = {
                    'message': 'Explain the building elements shown and their compliance requirements',
                    'session_id': self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat/vision", files=files, data=data)
                
                if response.status_code == 200:
                    vision_response = response.json()
                    ai_response = vision_response.get('response', '').lower()
                    
                    # Check for NZ-specific terminology
                    nz_terms = ['mate', 'bro', 'kiwi', 'new zealand', 'nz building code', 'nzbc']
                    building_terms = ['hearth', 'clearance', 'weathertight', 'insulation', 'compliance', 'clause']
                    tradie_terms = ['installation', 'requirements', 'specifications', 'standards']
                    
                    has_nz_terms = any(term in ai_response for term in nz_terms)
                    has_building_terms = sum(1 for term in building_terms if term in ai_response) >= 3
                    has_tradie_terms = any(term in ai_response for term in tradie_terms)
                    
                    if has_nz_terms and has_building_terms and has_tradie_terms:
                        self.log_test("NZ Building Terminology", True, "Response includes proper NZ building terminology", {
                            "nz_context": has_nz_terms,
                            "building_terms": has_building_terms,
                            "tradie_friendly": has_tradie_terms
                        })
                        os.unlink(test_image_path)
                        return True
                    else:
                        self.log_test("NZ Building Terminology", False, "Missing expected NZ terminology", {
                            "has_nz_terms": has_nz_terms,
                            "has_building_terms": has_building_terms,
                            "has_tradie_terms": has_tradie_terms,
                            "response_preview": ai_response[:200]
                        })
                        os.unlink(test_image_path)
                        return False
                else:
                    self.log_test("NZ Building Terminology", False, f"HTTP {response.status_code}", response.text)
                    os.unlink(test_image_path)
                    return False
                    
        except Exception as e:
            self.log_test("NZ Building Terminology", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling_invalid_file(self):
        """Test error handling for invalid file types"""
        try:
            # Test with non-image file
            invalid_file_path = self.create_invalid_file()
            if not invalid_file_path:
                self.log_test("Invalid File Error Handling", False, "Failed to create invalid file")
                return False
            
            with open(invalid_file_path, 'rb') as file:
                files = {'file': ('test.txt', file, 'text/plain')}
                data = {'message': 'Analyze this file'}
                
                response = self.session.post(f"{API_BASE}/chat/vision", files=files, data=data)
                
                # Should return 400 error for invalid file type
                if response.status_code == 400:
                    error_response = response.json()
                    if 'image' in error_response.get('detail', '').lower():
                        self.log_test("Invalid File Error Handling", True, "Properly rejected non-image file with 400 error")
                        os.unlink(invalid_file_path)
                        return True
                    else:
                        self.log_test("Invalid File Error Handling", False, "Error message doesn't mention image requirement", error_response)
                        os.unlink(invalid_file_path)
                        return False
                else:
                    self.log_test("Invalid File Error Handling", False, f"Expected 400, got {response.status_code}", response.text)
                    os.unlink(invalid_file_path)
                    return False
                    
        except Exception as e:
            self.log_test("Invalid File Error Handling", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling_missing_file(self):
        """Test error handling for missing file"""
        try:
            # Test without file
            data = {'message': 'Analyze this image'}
            
            response = self.session.post(f"{API_BASE}/chat/vision", data=data)
            
            # Should return 422 error for missing required file
            if response.status_code == 422:
                self.log_test("Missing File Error Handling", True, "Properly handled missing file with 422 error")
                return True
            else:
                self.log_test("Missing File Error Handling", False, f"Expected 422, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Missing File Error Handling", False, f"Error: {str(e)}")
            return False
    
    def test_large_file_handling(self):
        """Test handling of large image files"""
        try:
            large_image_path = self.create_large_image()
            if not large_image_path:
                self.log_test("Large File Handling", False, "Failed to create large image")
                return False
            
            # Check file size
            file_size = os.path.getsize(large_image_path)
            print(f"   Testing with {file_size / (1024*1024):.1f}MB image")
            
            with open(large_image_path, 'rb') as img_file:
                files = {'file': ('large_diagram.png', img_file, 'image/png')}
                data = {'message': 'Analyze this large construction diagram'}
                
                # Set longer timeout for large files
                response = self.session.post(f"{API_BASE}/chat/vision", files=files, data=data, timeout=60)
                
                if response.status_code == 200:
                    vision_response = response.json()
                    processing_time = vision_response.get('processing_time_ms', 0)
                    
                    self.log_test("Large File Handling", True, f"Successfully processed large image in {processing_time:.0f}ms", {
                        "file_size_mb": file_size / (1024*1024),
                        "processing_time_ms": processing_time
                    })
                    os.unlink(large_image_path)
                    return True
                elif response.status_code == 413:
                    self.log_test("Large File Handling", True, "Properly rejected oversized file with 413 error")
                    os.unlink(large_image_path)
                    return True
                else:
                    self.log_test("Large File Handling", False, f"Unexpected response: {response.status_code}", response.text)
                    os.unlink(large_image_path)
                    return False
                    
        except requests.exceptions.Timeout:
            self.log_test("Large File Handling", False, "Request timed out - may indicate server issue with large files")
            return False
        except Exception as e:
            self.log_test("Large File Handling", False, f"Error: {str(e)}")
            return False
    
    def test_default_message_handling(self):
        """Test vision endpoint with no message (should use default)"""
        try:
            test_image_path = self.create_test_construction_diagram()
            if not test_image_path:
                self.log_test("Default Message Handling", False, "Failed to create test image")
                return False
            
            with open(test_image_path, 'rb') as img_file:
                files = {'file': ('diagram.png', img_file, 'image/png')}
                # No message provided - should use default
                
                response = self.session.post(f"{API_BASE}/chat/vision", files=files)
                
                if response.status_code == 200:
                    vision_response = response.json()
                    ai_response = vision_response.get('response', '')
                    
                    # Should still provide analysis with default message
                    if ai_response and len(ai_response) > 100:
                        self.log_test("Default Message Handling", True, "Used default message and provided analysis", {
                            "response_length": len(ai_response)
                        })
                        os.unlink(test_image_path)
                        return True
                    else:
                        self.log_test("Default Message Handling", False, "No meaningful response with default message")
                        os.unlink(test_image_path)
                        return False
                else:
                    self.log_test("Default Message Handling", False, f"HTTP {response.status_code}", response.text)
                    os.unlink(test_image_path)
                    return False
                    
        except Exception as e:
            self.log_test("Default Message Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Vision AI tests"""
        print(f"\n🔍 Starting STRYDA.ai Vision AI Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Session ID: {self.session_id}")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            ("Vision Endpoint Basic Functionality", self.test_vision_endpoint_basic),
            ("GPT-4O Model Integration", self.test_gpt4o_integration),
            ("NZ Building Terminology", self.test_nz_building_terminology),
            ("Invalid File Error Handling", self.test_error_handling_invalid_file),
            ("Missing File Error Handling", self.test_error_handling_missing_file),
            ("Large File Handling", self.test_large_file_handling),
            ("Default Message Handling", self.test_default_message_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        
        print("\n" + "=" * 60)
        print(f"🏁 Vision AI Test Summary: {passed}/{total} tests passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = VisionAITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All Vision AI tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some Vision AI tests failed!")
        exit(1)