"""Example script to test the Invoices-Agent API."""

import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000/api/v1"


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_check_emails():
    """Test email checking endpoint."""
    print("Testing check emails endpoint...")
    payload = {
        "max_emails": 5,
        "unread_only": True
    }
    response = requests.post(f"{BASE_URL}/check-emails", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_classify(file_path: str):
    """Test document classification endpoint."""
    print(f"Testing classify endpoint with {file_path}...")
    payload = {
        "file_path": file_path
    }
    response = requests.post(f"{BASE_URL}/classify", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_upload_and_classify(file_path: str):
    """Test upload and classify endpoint."""
    print(f"Testing upload and classify with {file_path}...")
    
    if not Path(file_path).exists():
        print(f"File not found: {file_path}\n")
        return
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/upload-and-classify", files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_stats():
    """Test statistics endpoint."""
    print("Testing stats endpoint...")
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Invoices-Agent API Test Suite")
    print("=" * 60 + "\n")
    
    # Test health
    test_health()
    
    # Test stats
    test_stats()
    
    # Test email checking (requires proper credentials)
    # Uncomment to test:
    # test_check_emails()
    
    # Test file upload (provide a sample file path)
    # Uncomment and provide a file path:
    # test_upload_and_classify("path/to/sample/invoice.pdf")
    
    print("=" * 60)
    print("Test suite completed!")
    print("=" * 60)
