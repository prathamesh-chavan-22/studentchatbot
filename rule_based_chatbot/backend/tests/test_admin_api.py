import re


def test_admin_dashboard_is_served_from_backend(client):
    response = client.get("/admin")
    assert response.status_code == 200

    html = response.text
    script_match = re.search(r'src="(?P<src>/admin/assets/[^"]+)"', html)
    assert script_match is not None

    assets_response = client.get(script_match.group("src"))
    assert assets_response.status_code == 200


def test_admin_routes_require_auth(client):
    response = client.get("/api/admin/qna")
    assert response.status_code == 401


def test_admin_login_success_and_failure(client):
    bad = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert bad.status_code == 401

    good = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert good.status_code == 200
    assert good.json()["username"] == "admin"


def test_admin_qna_crud(client):
    client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "admin123"},
    )
    created = client.post(
        "/api/admin/qna",
        json={"question": "Original Q", "answer": "Original A"},
    )
    assert created.status_code == 201
    qna_id = created.json()["id"]

    listed = client.get("/api/admin/qna")
    assert listed.status_code == 200
    assert any(item["id"] == qna_id for item in listed.json())

    updated = client.put(
        f"/api/admin/qna/{qna_id}",
        json={"question": "Updated Q", "answer": "Updated A"},
    )
    assert updated.status_code == 200
    assert updated.json()["question"] == "Updated Q"

    deleted = client.delete(f"/api/admin/qna/{qna_id}")
    assert deleted.status_code == 204
