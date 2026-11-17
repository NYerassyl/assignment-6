def test_course_catalog_is_public_and_nested(client, catalog):
    courses = client.get("/api/courses")
    assert courses.status_code == 200
    body = courses.json()["courses"]
    assert len(body) == 1
    assert body[0]["topics"][0]["lessons"][0]["title"] == "Functions"

    lesson = client.get(f"/api/lessons/{catalog['lesson']['lesson_id']}")
    assert lesson.status_code == 200
    detail = lesson.json()["lesson"]
    assert detail["problems"][0]["title"] == "Add two numbers"
    assert "expected_answer" not in detail["problems"][0]


def test_crud_requires_authentication(client, catalog):
    anonymous = client.post("/api/courses", json={"title": "X", "language": "python"})
    assert anonymous.status_code == 401

    missing = client.get("/api/lessons/999999")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "LESSON_NOT_FOUND"


def test_update_and_validation_rules(client, catalog):
    headers = catalog["headers"]
    updated = client.patch(
        f"/api/problems/{catalog['problem']['id']}",
        json={"reward_xp": 25},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["problem"]["reward_xp"] == 25

    invalid = client.patch(
        f"/api/problems/{catalog['problem']['id']}",
        json={"reward_xp": -5},
        headers=headers,
    )
    assert invalid.status_code == 422


def test_unique_positions_are_enforced(client, catalog):
    headers = catalog["headers"]
    duplicate = client.post(
        f"/api/courses/{catalog['course']['id']}/topics",
        json={"title": "Duplicate", "position": 0},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONTENT_CONFLICT"


def test_prerequisite_cycles_are_rejected(client, catalog):
    headers = catalog["headers"]
    first = catalog["lesson"]["lesson_id"]
    second = client.post(
        f"/api/topics/{catalog['topic']['id']}/lessons",
        json={"title": "Lists", "theory_md": "theory", "position": 1, "prerequisite_id": first},
        headers=headers,
    ).json()["lesson_id"]

    cycle = client.patch(
        f"/api/lessons/{first}",
        json={"prerequisite_id": second},
        headers=headers,
    )
    assert cycle.status_code == 409
    assert cycle.json()["error"]["code"] == "PREREQUISITE_CYCLE"

    self_cycle = client.patch(
        f"/api/lessons/{first}",
        json={"prerequisite_id": first},
        headers=headers,
    )
    assert self_cycle.status_code == 409
