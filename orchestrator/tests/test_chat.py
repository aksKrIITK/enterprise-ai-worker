from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_endpoint_mock_openai():
    payload = {
        "conversation_id": "conv-123",
        "messages": [
            {"role": "user", "content": "Hello Enterprise AI"}
        ],
        "provider": "openai"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == "conv-123"
    assert "response" in data
    assert data["provider"] in ["openai", "openai-mock"]


def test_chat_endpoint_mock_gemini():
    payload = {
        "conversation_id": "conv-456",
        "messages": [
            {"role": "user", "content": "Hello Gemini Agent"}
        ],
        "provider": "gemini"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == "conv-456"
    assert "response" in data
    assert data["provider"] in ["gemini", "gemini-mock"]
