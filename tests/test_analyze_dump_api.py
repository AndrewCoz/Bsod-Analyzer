import io
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_analyze_dump_no_file(client):
    resp = client.post("/api/analyze-dump", data={})
    assert resp.status_code == 400

def test_analyze_dump_small_file(client):
    data = {
      'dumpFile': (io.BytesIO(b"\x00"*500_000), 'small.dmp')
    }
    resp = client.post("/api/analyze-dump", data=data, content_type='multipart/form-data')
    body = resp.get_json()
    assert resp.status_code == 200
    # Heuristic should pick MEMORY_MANAGEMENT (0x1A)
    assert body["code"] == "MEMORY_MANAGEMENT"
