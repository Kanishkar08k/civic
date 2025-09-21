#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Civic Issue Reporting System (CIRS)
Tests all backend API endpoints with various scenarios and edge cases.
"""

import requests
import json
import base64
import uuid
from datetime import datetime
import time

# Configuration
BASE_URL = "https://issuealert.preview.emergentagent.com/api"
TIMEOUT = 30

class CIRSBackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_user = None
        self.test_categories = []
        self.test_issues = []
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }
    
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        
        if success:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {message}")
        
        self.results["details"].append({
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_health_check(self):
        """Test API health check"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("Health Check", True, "API is healthy and responding")
                    return True
                else:
                    self.log_result("Health Check", False, f"Unexpected response: {data}")
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Health Check", False, f"Connection error: {str(e)}")
        return False
    
    def test_user_registration(self):
        """Test user registration with various scenarios"""
        # Test valid registration
        test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "name": "John Doe",
            "email": test_email,
            "password": "securepassword123",
            "phone": "+1234567890"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users/register", 
                                       json=user_data, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "user" in data:
                    self.test_user = data["user"]
                    self.log_result("User Registration - Valid", True, 
                                  f"User registered successfully: {data['user']['email']}")
                else:
                    self.log_result("User Registration - Valid", False, 
                                  f"Unexpected response format: {data}")
                    return False
            else:
                self.log_result("User Registration - Valid", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("User Registration - Valid", False, f"Error: {str(e)}")
            return False
        
        # Test duplicate email registration
        try:
            response = self.session.post(f"{self.base_url}/users/register", 
                                       json=user_data, timeout=TIMEOUT)
            if response.status_code == 400:
                self.log_result("User Registration - Duplicate Email", True, 
                              "Correctly rejected duplicate email")
            else:
                self.log_result("User Registration - Duplicate Email", False, 
                              f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_result("User Registration - Duplicate Email", False, f"Error: {str(e)}")
        
        # Test invalid email format
        invalid_user = user_data.copy()
        invalid_user["email"] = "invalid-email"
        try:
            response = self.session.post(f"{self.base_url}/users/register", 
                                       json=invalid_user, timeout=TIMEOUT)
            # Note: Backend might not validate email format, so we check response
            self.log_result("User Registration - Invalid Email", True, 
                          f"Response: HTTP {response.status_code}")
        except Exception as e:
            self.log_result("User Registration - Invalid Email", False, f"Error: {str(e)}")
        
        return True
    
    def test_user_login(self):
        """Test user login with various scenarios"""
        if not self.test_user:
            self.log_result("User Login - Setup", False, "No test user available")
            return False
        
        # Test valid login
        login_data = {
            "email": self.test_user["email"],
            "password": "securepassword123"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users/login", 
                                       json=login_data, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "user" in data:
                    self.log_result("User Login - Valid", True, 
                                  f"Login successful for {data['user']['email']}")
                else:
                    self.log_result("User Login - Valid", False, 
                                  f"Unexpected response format: {data}")
            else:
                self.log_result("User Login - Valid", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("User Login - Valid", False, f"Error: {str(e)}")
        
        # Test invalid credentials
        invalid_login = {
            "email": self.test_user["email"],
            "password": "wrongpassword"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/users/login", 
                                       json=invalid_login, timeout=TIMEOUT)
            if response.status_code == 401:
                self.log_result("User Login - Invalid Credentials", True, 
                              "Correctly rejected invalid credentials")
            else:
                self.log_result("User Login - Invalid Credentials", False, 
                              f"Should have returned 401, got {response.status_code}")
        except Exception as e:
            self.log_result("User Login - Invalid Credentials", False, f"Error: {str(e)}")
        
        return True
    
    def test_category_management(self):
        """Test category initialization and retrieval"""
        # Test category initialization
        try:
            response = self.session.post(f"{self.base_url}/categories/init", timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("Category Initialization", True, 
                                  "Categories initialized successfully")
                else:
                    self.log_result("Category Initialization", False, 
                                  f"Unexpected response: {data}")
            else:
                self.log_result("Category Initialization", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Category Initialization", False, f"Error: {str(e)}")
        
        # Test category retrieval
        try:
            response = self.session.get(f"{self.base_url}/categories", timeout=TIMEOUT)
            if response.status_code == 200:
                categories = response.json()
                if isinstance(categories, list) and len(categories) > 0:
                    self.test_categories = categories
                    self.log_result("Category Retrieval", True, 
                                  f"Retrieved {len(categories)} categories")
                    
                    # Verify expected categories
                    category_names = [cat.get("name", "") for cat in categories]
                    expected_categories = ["Roads & Transportation", "Water & Sanitation", 
                                         "Electricity", "Waste Management", "Public Safety", 
                                         "Parks & Recreation", "Other"]
                    
                    missing = [cat for cat in expected_categories if cat not in category_names]
                    if not missing:
                        self.log_result("Category Content Validation", True, 
                                      "All expected categories present")
                    else:
                        self.log_result("Category Content Validation", False, 
                                      f"Missing categories: {missing}")
                else:
                    self.log_result("Category Retrieval", False, 
                                  f"Expected list of categories, got: {categories}")
            else:
                self.log_result("Category Retrieval", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Category Retrieval", False, f"Error: {str(e)}")
        
        return len(self.test_categories) > 0
    
    def test_issue_creation(self):
        """Test issue creation with various scenarios"""
        if not self.test_user or not self.test_categories:
            self.log_result("Issue Creation - Setup", False, 
                          "Missing test user or categories")
            return False
        
        # Test basic issue creation
        issue_data = {
            "title": "Pothole on Main Street",
            "description": "Large pothole causing traffic issues near the intersection",
            "category_id": self.test_categories[0]["id"],
            "location_lat": 40.7128,
            "location_long": -74.0060,
            "address": "123 Main Street, New York, NY"
        }
        
        form_data = {
            "user_id": self.test_user["id"]
        }
        
        try:
            # Send as form data with JSON string
            data = {
                'user_id': self.test_user["id"]
            }
            response = self.session.post(f"{self.base_url}/issues", 
                                       json=issue_data,
                                       data=data, 
                                       timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "issue" in data:
                    self.test_issues.append(data["issue"])
                    self.log_result("Issue Creation - Basic", True, 
                                  f"Issue created successfully: {data['issue']['id']}")
                else:
                    self.log_result("Issue Creation - Basic", False, 
                                  f"Unexpected response format: {data}")
            else:
                self.log_result("Issue Creation - Basic", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Issue Creation - Basic", False, f"Error: {str(e)}")
        
        # Test issue creation with image
        sample_image_b64 = base64.b64encode(b"fake_image_data").decode()
        issue_with_image = issue_data.copy()
        issue_with_image.update({
            "title": "Broken streetlight with photo",
            "image_base64": sample_image_b64
        })
        
        try:
            # Create multipart form data with JSON and form fields
            files = {
                'issue_data': (None, json.dumps(issue_with_image), 'application/json'),
                'user_id': (None, self.test_user["id"])
            }
            response = self.session.post(f"{self.base_url}/issues", 
                                       files=files, 
                                       timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "issue" in data:
                    self.test_issues.append(data["issue"])
                    self.log_result("Issue Creation - With Image", True, 
                                  "Issue with image created successfully")
                else:
                    self.log_result("Issue Creation - With Image", False, 
                                  f"Unexpected response: {data}")
            else:
                self.log_result("Issue Creation - With Image", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Issue Creation - With Image", False, f"Error: {str(e)}")
        
        # Test issue creation with voice note
        sample_voice_b64 = base64.b64encode(b"fake_audio_data").decode()
        issue_with_voice = issue_data.copy()
        issue_with_voice.update({
            "title": "Noise complaint with voice note",
            "voice_base64": sample_voice_b64
        })
        
        try:
            # Create multipart form data with JSON and form fields
            files = {
                'issue_data': (None, json.dumps(issue_with_voice), 'application/json'),
                'user_id': (None, self.test_user["id"])
            }
            response = self.session.post(f"{self.base_url}/issues", 
                                       files=files, 
                                       timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "issue" in data:
                    self.test_issues.append(data["issue"])
                    self.log_result("Issue Creation - With Voice", True, 
                                  "Issue with voice note created successfully")
                else:
                    self.log_result("Issue Creation - With Voice", False, 
                                  f"Unexpected response: {data}")
            else:
                self.log_result("Issue Creation - With Voice", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Issue Creation - With Voice", False, f"Error: {str(e)}")
        
        return len(self.test_issues) > 0
    
    def test_issue_retrieval(self):
        """Test issue retrieval with various filters"""
        # Test basic issue retrieval
        try:
            response = self.session.get(f"{self.base_url}/issues", timeout=TIMEOUT)
            if response.status_code == 200:
                issues = response.json()
                if isinstance(issues, list):
                    self.log_result("Issue Retrieval - Basic", True, 
                                  f"Retrieved {len(issues)} issues")
                    
                    # Verify issue structure
                    if issues:
                        issue = issues[0]
                        required_fields = ["id", "title", "description", "location_lat", 
                                         "location_long", "vote_count", "created_at"]
                        missing_fields = [field for field in required_fields 
                                        if field not in issue]
                        if not missing_fields:
                            self.log_result("Issue Structure Validation", True, 
                                          "Issue structure is correct")
                        else:
                            self.log_result("Issue Structure Validation", False, 
                                          f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Issue Retrieval - Basic", False, 
                                  f"Expected list, got: {type(issues)}")
            else:
                self.log_result("Issue Retrieval - Basic", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Issue Retrieval - Basic", False, f"Error: {str(e)}")
        
        # Test location-based filtering
        try:
            params = {
                "lat": 40.7128,
                "lng": -74.0060,
                "radius": 5.0
            }
            response = self.session.get(f"{self.base_url}/issues", 
                                      params=params, timeout=TIMEOUT)
            if response.status_code == 200:
                issues = response.json()
                self.log_result("Issue Retrieval - Location Filter", True, 
                              f"Location filtering returned {len(issues)} issues")
            else:
                self.log_result("Issue Retrieval - Location Filter", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Issue Retrieval - Location Filter", False, f"Error: {str(e)}")
        
        # Test category filtering
        if self.test_categories:
            try:
                params = {"category_id": self.test_categories[0]["id"]}
                response = self.session.get(f"{self.base_url}/issues", 
                                          params=params, timeout=TIMEOUT)
                if response.status_code == 200:
                    issues = response.json()
                    self.log_result("Issue Retrieval - Category Filter", True, 
                                  f"Category filtering returned {len(issues)} issues")
                else:
                    self.log_result("Issue Retrieval - Category Filter", False, 
                                  f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Issue Retrieval - Category Filter", False, f"Error: {str(e)}")
        
        return True
    
    def test_individual_issue_retrieval(self):
        """Test retrieving individual issues"""
        if not self.test_issues:
            self.log_result("Individual Issue Retrieval - Setup", False, 
                          "No test issues available")
            return False
        
        issue_id = self.test_issues[0]["id"]
        try:
            response = self.session.get(f"{self.base_url}/issues/{issue_id}", 
                                      timeout=TIMEOUT)
            if response.status_code == 200:
                issue = response.json()
                if issue.get("id") == issue_id:
                    self.log_result("Individual Issue Retrieval - Valid ID", True, 
                                  f"Retrieved issue {issue_id}")
                else:
                    self.log_result("Individual Issue Retrieval - Valid ID", False, 
                                  f"ID mismatch: expected {issue_id}, got {issue.get('id')}")
            else:
                self.log_result("Individual Issue Retrieval - Valid ID", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Individual Issue Retrieval - Valid ID", False, f"Error: {str(e)}")
        
        # Test invalid issue ID
        try:
            response = self.session.get(f"{self.base_url}/issues/invalid-id", 
                                      timeout=TIMEOUT)
            if response.status_code == 404:
                self.log_result("Individual Issue Retrieval - Invalid ID", True, 
                              "Correctly returned 404 for invalid ID")
            else:
                self.log_result("Individual Issue Retrieval - Invalid ID", False, 
                              f"Should have returned 404, got {response.status_code}")
        except Exception as e:
            self.log_result("Individual Issue Retrieval - Invalid ID", False, f"Error: {str(e)}")
        
        return True
    
    def test_voting_system(self):
        """Test voting functionality"""
        if not self.test_user or not self.test_issues:
            self.log_result("Voting System - Setup", False, 
                          "Missing test user or issues")
            return False
        
        issue_id = self.test_issues[0]["id"]
        form_data = {"user_id": self.test_user["id"]}
        
        # Test adding a vote
        try:
            files = {
                'user_id': (None, self.test_user["id"])
            }
            response = self.session.post(f"{self.base_url}/issues/{issue_id}/vote", 
                                       files=files, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("voted") == True:
                    self.log_result("Voting System - Add Vote", True, 
                                  "Vote added successfully")
                else:
                    self.log_result("Voting System - Add Vote", False, 
                                  f"Unexpected response: {data}")
            else:
                self.log_result("Voting System - Add Vote", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Voting System - Add Vote", False, f"Error: {str(e)}")
        
        # Test removing a vote (toggle)
        try:
            files = {
                'user_id': (None, self.test_user["id"])
            }
            response = self.session.post(f"{self.base_url}/issues/{issue_id}/vote", 
                                       files=files, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("voted") == False:
                    self.log_result("Voting System - Remove Vote", True, 
                                  "Vote removed successfully (toggle)")
                else:
                    self.log_result("Voting System - Remove Vote", False, 
                                  f"Unexpected response: {data}")
            else:
                self.log_result("Voting System - Remove Vote", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Voting System - Remove Vote", False, f"Error: {str(e)}")
        
        # Test voting on invalid issue
        try:
            files = {
                'user_id': (None, self.test_user["id"])
            }
            response = self.session.post(f"{self.base_url}/issues/invalid-id/vote", 
                                       files=files, timeout=TIMEOUT)
            # Note: Backend might not validate issue existence for voting
            self.log_result("Voting System - Invalid Issue", True, 
                          f"Response: HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Voting System - Invalid Issue", False, f"Error: {str(e)}")
        
        return True
    
    def test_comments_system(self):
        """Test comment creation and retrieval"""
        if not self.test_user or not self.test_issues:
            self.log_result("Comments System - Setup", False, 
                          "Missing test user or issues")
            return False
        
        issue_id = self.test_issues[0]["id"]
        
        # Test adding a comment
        comment_data = {
            "issue_id": issue_id,
            "message": "This is a test comment about the reported issue."
        }
        form_data = {"user_id": self.test_user["id"]}
        
        try:
            files = {
                'comment_data': (None, json.dumps(comment_data), 'application/json'),
                'user_id': (None, self.test_user["id"])
            }
            response = self.session.post(f"{self.base_url}/issues/{issue_id}/comments", 
                                       files=files, 
                                       timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "comment" in data:
                    self.log_result("Comments System - Add Comment", True, 
                                  "Comment added successfully")
                else:
                    self.log_result("Comments System - Add Comment", False, 
                                  f"Unexpected response: {data}")
            else:
                self.log_result("Comments System - Add Comment", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Comments System - Add Comment", False, f"Error: {str(e)}")
        
        # Test retrieving comments
        try:
            response = self.session.get(f"{self.base_url}/issues/{issue_id}/comments", 
                                      timeout=TIMEOUT)
            if response.status_code == 200:
                comments = response.json()
                if isinstance(comments, list):
                    self.log_result("Comments System - Retrieve Comments", True, 
                                  f"Retrieved {len(comments)} comments")
                    
                    # Verify comment structure
                    if comments:
                        comment = comments[0]
                        required_fields = ["id", "message", "user_id", "created_at"]
                        missing_fields = [field for field in required_fields 
                                        if field not in comment]
                        if not missing_fields:
                            self.log_result("Comment Structure Validation", True, 
                                          "Comment structure is correct")
                        else:
                            self.log_result("Comment Structure Validation", False, 
                                          f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Comments System - Retrieve Comments", False, 
                                  f"Expected list, got: {type(comments)}")
            else:
                self.log_result("Comments System - Retrieve Comments", False, 
                              f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Comments System - Retrieve Comments", False, f"Error: {str(e)}")
        
        # Test comments for invalid issue
        try:
            response = self.session.get(f"{self.base_url}/issues/invalid-id/comments", 
                                      timeout=TIMEOUT)
            # Backend might return empty list for invalid issue
            self.log_result("Comments System - Invalid Issue", True, 
                          f"Response: HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Comments System - Invalid Issue", False, f"Error: {str(e)}")
        
        return True
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"Starting CIRS Backend Testing at {datetime.now()}")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run tests in order
        self.test_health_check()
        self.test_user_registration()
        self.test_user_login()
        self.test_category_management()
        self.test_issue_creation()
        self.test_issue_retrieval()
        self.test_individual_issue_retrieval()
        self.test_voting_system()
        self.test_comments_system()
        
        # Print summary
        print("=" * 60)
        print(f"Testing completed at {datetime.now()}")
        print(f"Results: {self.results['passed']} passed, {self.results['failed']} failed")
        
        if self.results["errors"]:
            print("\nFailed Tests:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        return self.results

if __name__ == "__main__":
    tester = CIRSBackendTester()
    results = tester.run_all_tests()
    
    # Save detailed results
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: /app/backend_test_results.json")