import os
import sys
from unittest.mock import MagicMock

# Mock out the service modules before importing main to avoid real network connections
# during test initialization
mock_gemini = MagicMock()
sys.modules['gemini_service'] = mock_gemini

mock_weaviate = MagicMock()
sys.modules['weaviate_service'] = mock_weaviate

# Set dummy environment variables just in case
os.environ["GEMINI_API_KEY"] = "dummy"
os.environ["WEAVIATE_API_KEY"] = "dummy"
os.environ["WEAVIATE_URL"] = "http://dummy.url"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "services": {
            "gemini": "connected",
            "weaviate": "connected"
        }
    }
