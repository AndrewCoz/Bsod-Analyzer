import json
import pytest
from app import app, error_codes_data

@pytest.fixture
def client():
    # I'm setting up my Flask test client here
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_analyze_code_exact_match(client):
    # I'm testing how my API handles an exact match for a BSOD error code
    # I know MEMORY_MANAGEMENT exists in my error_codes_data 
    resp = client.post("/api/analyze-code",
                      data=json.dumps({"errorCode": "MEMORY_MANAGEMENT"}),
                      content_type="application/json")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["code"] == "MEMORY_MANAGEMENT"

def test_analyze_code_generic_fallback(client):
    # I'm testing if my API correctly returns a generic response for unknown error codes
    resp = client.post("/api/analyze-code",
                      data=json.dumps({"errorCode": "UNKNOWN_CODE"}),
                      content_type="application/json")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "Generic BSOD" in body["description"] 