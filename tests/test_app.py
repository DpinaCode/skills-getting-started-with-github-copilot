from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


TEST_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete",
        "schedule": "Fridays",
        "max_participants": 4,
        "participants": ["existing@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore visual art",
        "schedule": "Mondays",
        "max_participants": 5,
        "participants": [],
    },
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(TEST_ACTIVITIES))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    # Arrange
    path = "/activities"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    assert response.json() == TEST_ACTIVITIES


def test_signup_adds_participant(client):
    # Arrange
    email = "new@mergington.edu"
    path = f"/activities/{quote('Chess Club', safe='')}/signup"

    # Act
    response = client.post(path, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities_response.json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    path = f"/activities/{quote('Chess Club', safe='')}/signup"
    email = "existing@mergington.edu"

    # Act
    response = client.post(path, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_signup_rejects_unknown_activity(client):
    # Arrange
    path = "/activities/Unknown%20Club/signup"
    email = "new@mergington.edu"

    # Act
    response = client.post(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    # Arrange
    path = f"/activities/{quote('Chess Club', safe='')}/signup"
    email = "existing@mergington.edu"

    # Act
    response = client.delete(path, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@mergington.edu from Chess Club"
    }
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_rejects_missing_participant(client):
    # Arrange
    path = f"/activities/{quote('Chess Club', safe='')}/signup"
    email = "missing@mergington.edu"

    # Act
    response = client.delete(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    path = "/activities/Unknown%20Club/signup"
    email = "new@mergington.edu"

    # Act
    response = client.delete(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
