
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from app.main import app


client = TestClient(app)


client = TestClient(app)


def test_create_report():
    response = client.post(
        "/reports",
        json={
            "category": "Technical",
            "description": "This is a test report for automated testing.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["case_code"].startswith("WD-")
    assert data["status"] == "SUBMITTED"


def test_track_invalid_case_code():
    response = client.get("/reports/WD-NOPE-NOPE-NOPE-NOPE")

    assert response.status_code == 404
    assert response.json()["detail"] == "No report found for that case code."


def test_invalid_status_transition():
    create_response = client.post(
        "/reports",
        json={
            "category": "Technical",
            "description": "Report created for transition testing.",
        },
    )

    assert create_response.status_code == 201

    case_code = create_response.json()["case_code"]

    # First move: SUBMITTED → UNDER_REVIEW
    response = client.patch(
        f"/reports/{case_code}",
        json={
            "status": "UNDER_REVIEW",
            "status_update": "Review started.",
        },
    )

    # This endpoint requires moderator authentication,
    # so an unauthenticated request should be rejected.
    assert response.status_code == 401


def test_track_created_report():
    create_response = client.post(
        "/reports",
        json={
            "category": "Technical",
            "description": "Report created for tracking test.",
        },
    )

    assert create_response.status_code == 201

    case_code = create_response.json()["case_code"]

    response = client.get(f"/reports/{case_code}")

    assert response.status_code == 200

    data = response.json()

    assert data["case_code"] == case_code
    assert data["status"] == "SUBMITTED"
    assert data["status_update"] is None


def test_moderator_login():
    from app.config import settings

    original_username = settings.moderator_username
    original_hash = settings.moderator_password_hash

    test_password = "TestPassword123!"
    settings.moderator_username = "test-moderator"
    settings.moderator_password_hash = PasswordHash.recommended().hash(test_password)

    try:
        response = client.post(
            "/auth/login",
            data={
                "username": "test-moderator",
                "password": test_password,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["token_type"] == "bearer"
        assert data["access_token"]
    finally:
        settings.moderator_username = original_username
        settings.moderator_password_hash = original_hash


def test_moderator_can_list_reports():
    from app.config import settings

    original_username = settings.moderator_username
    original_hash = settings.moderator_password_hash

    test_password = "TestPassword123!"
    settings.moderator_username = "test-moderator"
    settings.moderator_password_hash = PasswordHash.recommended().hash(test_password)

    try:
        login_response = client.post(
            "/auth/login",
            data={
                "username": "test-moderator",
                "password": test_password,
            },
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        response = client.get(
            "/reports",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        settings.moderator_username = original_username
        settings.moderator_password_hash = original_hash


def test_create_report_rejects_short_description():
    response = client.post(
        "/reports",
        json={
            "category": "Technical",
            "description": "Too short",
        },
    )

    assert response.status_code == 422


def test_create_report_rejects_missing_category():
    response = client.post(
        "/reports",
        json={
            "description": "This report has no category.",
        },
    )

    assert response.status_code == 422


def test_create_report_rejects_extra_fields():
    response = client.post(
        "/reports",
        json={
            "category": "Technical",
            "description": "This is a valid test report.",
            "unexpected_field": "should not be accepted",
        },
    )

    assert response.status_code == 422


def test_invalid_status_transition_automated():
    from app.config import settings

    original_username = settings.moderator_username
    original_hash = settings.moderator_password_hash

    test_password = "TestPassword123!"
    settings.moderator_username = "test-moderator"
    settings.moderator_password_hash = PasswordHash.recommended().hash(test_password)

    try:
        create_response = client.post(
            "/reports",
            json={
                "category": "Technical",
                "description": "Testing invalid status transition.",
            },
        )

        assert create_response.status_code == 201
        case_code = create_response.json()["case_code"]

        login_response = client.post(
            "/auth/login",
            data={
                "username": "test-moderator",
                "password": test_password,
            },
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = client.patch(
            f"/reports/{case_code}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "status": "RESOLVED",
                "status_update": "Invalid transition test.",
            },
        )

        assert response.status_code == 400

    finally:
        settings.moderator_username = original_username
        settings.moderator_password_hash = original_hash
