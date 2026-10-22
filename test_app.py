import os

import psycopg
import pytest

from app import create_app, init_db

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://appuser:apppassword@localhost:5432/appdb",
)


@pytest.fixture(scope="session")
def app():
    init_db(TEST_DATABASE_URL)
    return create_app({"TESTING": True, "DATABASE_URL": TEST_DATABASE_URL})


@pytest.fixture()
def client(app):
    with psycopg.connect(TEST_DATABASE_URL) as conn:
        conn.execute("DELETE FROM notes")
    return app.test_client()


def test_home_returns_application_info(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["application"] == "Automatyzacja deploymentu"


def test_health_is_healthy_when_database_is_available(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["database"] == "connected"


def test_create_and_list_note(client):
    create_response = client.post("/api/notes", json={"content": "Test CI/CD"})
    assert create_response.status_code == 201
    assert create_response.json["note"]["content"] == "Test CI/CD"

    list_response = client.get("/api/notes")
    assert list_response.status_code == 200
    assert any(item["content"] == "Test CI/CD" for item in list_response.json["items"])


def test_empty_note_is_rejected(client):
    response = client.post("/api/notes", json={"content": "   "})
    assert response.status_code == 400
    assert "wymagane" in response.json["error"]


def test_note_over_500_characters_is_rejected(client):
    response = client.post("/api/notes", json={"content": "x" * 501})
    assert response.status_code == 400
