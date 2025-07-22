"""
Enhanced Backend API Testing for Document Forgery Detection System
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
import logging
from dotenv import load_dotenv
from PIL import Image

# Load environment variables from .env
load_dotenv()
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CLI color helper
def color(text, code): return f"\033[{code}m{text}\033[0m"

class DocumentForgeryAPITester:
    def __init__(self, base_url=DEFAULT_BACKEND_URL):
        self.base_url = base_url.rstrip("/")
        self.tests_run = 0
        self.tests_passed = 0
        self.analysis_id = None
        self.test_image_path = "static/uploads/test_image.jpg"
        self._ensure_test_image()

    def _ensure_test_image(self):
        """Ensure a test image is available for upload"""
        if not os.path.exists(self.test_image_path):
            try:
                os.makedirs(os.path.dirname(self.test_image_path), exist_ok=True)
                logger.info("Downloading test image...")
                response = requests.get("https://picsum.photos/200/300", timeout=10)
                if response.status_code == 200:
                    with open(self.test_image_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Test image created at {self.test_image_path}")
                else:
                    logger.warning("Image download failed, generating blank image.")
                    self._create_blank_image()
            except Exception as e:
                logger.error(f"Error downloading image: {e}, generating fallback image.")
                self._create_blank_image()

    def _create_blank_image(self):
        img = Image.new('RGB', (200, 300), color='white')
        img.save(self.test_image_path)
        logger.info(f"Blank test image saved at {self.test_image_path}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Generic API test runner"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {}
        self.tests_run += 1

        logger.info(f"\n🔍 Testing: {name}")
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=10)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError("Unsupported HTTP method")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                logger.info(color(f"✅ Passed [{response.status_code}]", 32))
            else:
                logger.error(color(f"❌ Failed - Expected {expected_status}, got {response.status_code}", 31))

            try:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return success, response.json()
                return success, {"raw": response.text}
            except Exception:
                return success, {"error": "Invalid JSON"}

        except Exception as e:
            logger.error(color(f"❌ Request error: {e}", 31))
            return False, {}

    def test_api_root(self):
        return self.run_test("API Root", "GET", "", 200)

    def test_get_analyses(self):
        return self.run_test("Get Analyses", "GET", "analyses", 200)

    def test_analyze_document(self):
        if not os.path.exists(self.test_image_path):
            logger.error("Test image not found.")
            return False, {}

        with open(self.test_image_path, 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            success, response = self.run_test("Analyze Document", "POST", "analyze", 200, files=files)

        if success and response.get("success"):
            self.analysis_id = response.get("data", {}).get("id")
            logger.info(f"Verdict: {response['data'].get('verdict')} | Confidence: {response['data'].get('confidence')}%")
        return success, response

    def test_generate_report(self):
        if not self.analysis_id:
            logger.error("No analysis ID for report generation.")
            return False, {}

        return self.run_test("Generate Report", "GET", f"generate-report/{self.analysis_id}", 200)

    def summary(self):
        print("\n📊 TEST SUMMARY")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        return self.tests_passed == self.tests_run

    def save_results(self, path="test_results.json"):
        with open(path, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "tests_run": self.tests_run,
                "tests_passed": self.tests_passed
            }, f, indent=2)
        logger.info(f"Saved result summary to {path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Backend API Tester for Document Forgery Detector")
    parser.add_argument("--url", type=str, help="Override backend base URL")
    parser.add_argument("--save", action="store_true", help="Save results to JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    tester = DocumentForgeryAPITester(base_url=args.url or DEFAULT_BACKEND_URL)

    # Run tests
    root_success, _ = tester.test_api_root()
    analyses_success, _ = tester.test_get_analyses()
    analyze_success, _ = tester.test_analyze_document()
    report_success, _ = (tester.test_generate_report() if analyze_success else (False, {}))

    # Print individual results
    print("\n🔁 TEST RESULTS")
    print(f"API Root           : {'✅' if root_success else '❌'}")
    print(f"Get Analyses       : {'✅' if analyses_success else '❌'}")
    print(f"Analyze Document   : {'✅' if analyze_success else '❌'}")
    print(f"Generate Report    : {'✅' if report_success else '❌'}")

    tester.summary()

    if args.save:
        tester.save_results()

    return 0 if tester.tests_passed == tester.tests_run else 1


if __name__ == "__main__":
    sys.exit(main())
