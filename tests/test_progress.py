def test_start_creates_progress_row_and_overview(client, catalog):
    headers = catalog["headers"]
    lesson_id = catalog["lesson"]["lesson_id"]

    started = client.post(f"/api/lessons/{lesson_id}/start", headers=headers)
    assert started.status_code == 200
    body = started.json()
    assert body["lesson_id"] == lesson_id
    assert body["state"] == "IN_PROGRESS"
    assert body["completed_at"] is None

    repeat = client.post(f"/api/lessons/{lesson_id}/start", headers=headers)
    assert repeat.status_code == 200
    assert repeat.json()["started_at"] == body["started_at"]

    overview = client.get("/api/progress", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["lessons"] == [body]


def test_prerequisite_must_be_completed_first(client, catalog):
    headers = catalog["headers"]
    first = catalog["lesson"]["lesson_id"]
    second = client.post(
        f"/api/topics/{catalog['topic']['id']}/lessons",
        json={
            "title": "Advanced",
            "theory_md": "theory",
            "position": 1,
            "prerequisite_id": first,
        },
        headers=headers,
    ).json()["lesson_id"]

    blocked = client.post(f"/api/lessons/{second}/start", headers=headers)
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "PREREQUISITE_REQUIRED"

    accepted = client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": "def add(a, b):\n    return a + b\n"},
        headers=headers,
    )
    assert accepted.status_code == 201
    assert accepted.json()["lesson_completed"] is True

    allowed = client.post(f"/api/lessons/{second}/start", headers=headers)
    assert allowed.status_code == 200
    assert allowed.json()["state"] == "IN_PROGRESS"


def test_lesson_completion_requires_every_problem(client, catalog):
    headers = catalog["headers"]
    lesson_id = catalog["lesson"]["lesson_id"]
    client.post(f"/api/lessons/{lesson_id}/start", headers=headers)

    incomplete = client.post(f"/api/lessons/{lesson_id}/complete", headers=headers)
    assert incomplete.status_code == 409
    assert incomplete.json()["error"]["code"] == "LESSON_INCOMPLETE"

    client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": "def add(a, b):\n    return a + b"},
        headers=headers,
    )

    completed = client.post(f"/api/lessons/{lesson_id}/complete", headers=headers)
    assert completed.status_code == 200
    assert completed.json()["state"] == "COMPLETED"
    assert completed.json()["completed_at"] is not None

    reset = client.delete(f"/api/lessons/{lesson_id}/progress", headers=headers)
    assert reset.status_code == 409
    assert reset.json()["error"]["code"] == "COMPLETED_PROGRESS"


def test_reset_removes_started_progress(client, catalog):
    headers = catalog["headers"]
    lesson_id = catalog["lesson"]["lesson_id"]
    client.post(f"/api/lessons/{lesson_id}/start", headers=headers)

    reset = client.delete(f"/api/lessons/{lesson_id}/progress", headers=headers)
    assert reset.status_code == 204
    assert client.get("/api/progress", headers=headers).json()["lessons"] == []


def test_progress_requires_authentication(client, catalog):
    lesson_id = catalog["lesson"]["lesson_id"]
    assert client.post(f"/api/lessons/{lesson_id}/start").status_code == 401
    assert client.get("/api/progress").status_code == 401
