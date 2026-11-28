import os
import sys
import base64
import tempfile
import pytest
from fastapi.testclient import TestClient

os.environ["GEOATLAS_DATA_DIR"] = "/tmp/geoatlas_test"
os.environ["DUEL_DATA_DIR"] = "/tmp/geoatlas_test_duel"
os.environ["ENVIRONMENT"] = "development"
os.environ["MAIL_PROVIDER"] = "mock"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
import auth_service
from server import app, _rate_limit_store

server.DUEL_ROOMS_FILE = os.path.join(tempfile.gettempdir(), "geoatlas_test_duel_rooms.json")


@pytest.fixture
def anon_client():
    _rate_limit_store.clear()
    auth_service.MOCK_MAILBOX.clear()
    return TestClient(app)


@pytest.fixture
def client():
    _rate_limit_store.clear()
    auth_service.MOCK_MAILBOX.clear()
    cred = base64.b64encode(b"admin:admin").decode()
    tc = TestClient(app)
    tc.headers.update({"Authorization": f"Basic {cred}"})
    return tc


@pytest.fixture
def auth_headers():
    cred = base64.b64encode(b"admin:admin").decode()
    return {"Authorization": f"Basic {cred}"}
