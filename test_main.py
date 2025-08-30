import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_mask_messages():
    data = {
        "messages": [
            {"role": "user", "content": "My name is John Doe. Call me at 555-123-4567 or email john@gmail.com."}
        ]
    }
    response = client.post("/mask", json=data)
    assert response.status_code == 200
    masked = response.json()
    assert "John Doe" not in masked["messages"][0]["content"]
    assert "555-123-4567" not in masked["messages"][0]["content"]
    assert "john@example.com" not in masked["messages"][0]["content"]
    print(masked["messages"][0]["content"])

def test_mask_choices():
    data = {
        "choices": [
            {"message": {"role": "assistant", "content": "Contact me at jane@acme.com or 212-555-0100"}}
        ]
    }
    response = client.post("/mask", json=data)
    assert response.status_code == 200
    masked = response.json()
    assert "jane@acme.com" not in masked["choices"][0]["message"]["content"]
    assert "212-555-0100" not in masked["choices"][0]["message"]["content"]

def test_mask_empty_content():
    data = {"messages": [{"role": "user", "content": "   "}]}
    response = client.post("/mask", json=data)
    assert response.status_code == 200
    assert response.json()["messages"][0]["content"] == "   "
