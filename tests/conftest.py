import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

os.environ["GEOATLAS_DATA_DIR"] = "/tmp/geoatlas_test"
os.environ["DUEL_DATA_DIR"] = "/tmp/geoatlas_test_duel"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from server import app, _rate_limit_store

server.DUEL_ROOMS_FILE = os.path.join(tempfile.gettempdir(), "geoatlas_test_duel_rooms.json")

@pytest.fixture
def client():
    _rate_limit_store.clear()
    return TestClient(app)

@pytest.fixture
def auth_headers():
    import base64
    cred = base64.b64encode(b"admin:admin").decode()
    return {"Authorization": f"Basic {cred}"}
