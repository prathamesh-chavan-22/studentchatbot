def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_exact_match_returns_answer(client):
    login = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200

    create = client.post(
        "/api/admin/qna",
        json={"question": "What is FYJC?", "answer": "FYJC is class 11 admission."},
    )
    assert create.status_code == 201

    ask = client.post("/api/chat/ask", json={"message": "What is FYJC?"})
    assert ask.status_code == 200
    assert ask.json()["type"] == "answer"
    assert ask.json()["answer"] == "FYJC is class 11 admission."


def test_non_exact_returns_80_percent_match_suggestions(client):
    client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "admin123"},
    )
    rows = [
        ("What is FYJC?", "A1"),
        ("How to register online?", "A2"),
        ("What documents are required?", "A3"),
        ("What is admission schedule?", "A4"),
        ("Is there reservation quota?", "A5"),
    ]
    for q, a in rows:
        client.post("/api/admin/qna", json={"question": q, "answer": a})

    ask = client.post("/api/chat/ask", json={"message": "How to register online"})
    assert ask.status_code == 200
    data = ask.json()
    assert data["type"] == "suggestions"
    assert len(data["suggestions"]) > 0


def test_no_match_above_80_percent_returns_no_match_message(client):
    client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "admin123"},
    )
    rows = [
        ("What is FYJC?", "A1"),
        ("How to register online?", "A2"),
    ]
    for q, a in rows:
        client.post("/api/admin/qna", json={"question": q, "answer": a})

    ask = client.post("/api/chat/ask", json={"message": "tell me about xyz"})
    assert ask.status_code == 200
    data = ask.json()
    assert data["type"] == "no_match"
    assert "Please contact the FYJC center" in data["message"]


def test_select_returns_stored_answer_as_is(client):
    client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "admin123"},
    )
    created = client.post(
        "/api/admin/qna",
        json={"question": "Q", "answer": "Answer as stored."},
    ).json()

    selected = client.post("/api/chat/select", json={"qna_id": created["id"]})
    assert selected.status_code == 200
    assert selected.json()["type"] == "answer"
    assert selected.json()["answer"] == "Answer as stored."
