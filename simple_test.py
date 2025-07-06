"""
Simple test to check if the backend API is accessible
"""

import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://efbea9ff-373c-4a5f-a188-06bc28537e40.preview.emergentagent.com"

def test_api_root():
    """Test the API root endpoint"""
    url = f"{BACKEND_URL}/api/"
    logger.info(f"Testing API root at {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_api_root()