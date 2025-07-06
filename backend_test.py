"""
Backend API Testing for Document Forgery Detection System
"""

import requests
import os
import sys
import json
from datetime import datetime
import unittest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from frontend .env file
BACKEND_URL = "https://efbea9ff-373c-4a5f-a188-06bc28537e40.preview.emergentagent.com"

class DocumentForgeryAPITester:
    def __init__(self, base_url=BACKEND_URL):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_image_path = "/app/backend/static/uploads/test_image.jpg"
        self.analysis_id = None
        
        # Create a test image if it doesn't exist
        self._ensure_test_image()

    def _ensure_test_image(self):
        """Create a test image if it doesn't exist"""
        if not os.path.exists(self.test_image_path):
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.test_image_path), exist_ok=True)
                
                # Create a simple test image using requests
                logger.info("Downloading a test image...")
                response = requests.get("https://picsum.photos/200/300")
                if response.status_code == 200:
                    with open(self.test_image_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Test image created at {self.test_image_path}")
                else:
                    logger.error("Failed to download test image")
            except Exception as e:
                logger.error(f"Error creating test image: {e}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {}
        
        self.tests_run += 1
        logger.info(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                logger.info(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                logger.error(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    logger.error(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            logger.error(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test the API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        if success:
            logger.info(f"API Response: {response}")
        return success

    def test_get_analyses(self):
        """Test getting analyses"""
        success, response = self.run_test(
            "Get Analyses",
            "GET",
            "analyses",
            200
        )
        if success:
            logger.info(f"Found {len(response)} analyses")
        return success

    def test_analyze_document(self):
        """Test document analysis"""
        if not os.path.exists(self.test_image_path):
            logger.error(f"Test image not found at {self.test_image_path}")
            return False
            
        with open(self.test_image_path, 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            success, response = self.run_test(
                "Analyze Document",
                "POST",
                "analyze",
                200,
                files=files
            )
            
        if success and response.get('success'):
            self.analysis_id = response.get('data', {}).get('id')
            logger.info(f"Analysis ID: {self.analysis_id}")
            logger.info(f"Verdict: {response.get('data', {}).get('verdict')}")
            logger.info(f"Confidence: {response.get('data', {}).get('confidence')}%")
        return success and response.get('success', False)

    def test_generate_report(self):
        """Test PDF report generation"""
        if not self.analysis_id:
            logger.error("No analysis ID available for report generation")
            return False
            
        success, _ = self.run_test(
            "Generate PDF Report",
            "GET",
            f"generate-report/{self.analysis_id}",
            200
        )
        return success

def main():
    logger.info("Starting Document Forgery Detection API Tests")
    
    # Create tester instance
    tester = DocumentForgeryAPITester()
    
    # Run tests
    api_root_success = tester.test_api_root()
    get_analyses_success = tester.test_get_analyses()
    analyze_success = tester.test_analyze_document()
    report_success = False
    
    if analyze_success:
        report_success = tester.test_generate_report()
    
    # Print results
    logger.info("\n📊 Test Results:")
    logger.info(f"API Root: {'✅' if api_root_success else '❌'}")
    logger.info(f"Get Analyses: {'✅' if get_analyses_success else '❌'}")
    logger.info(f"Analyze Document: {'✅' if analyze_success else '❌'}")
    logger.info(f"Generate Report: {'✅' if report_success else '❌'}")
    logger.info(f"\nTests passed: {tester.tests_passed}/{tester.tests_run}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())