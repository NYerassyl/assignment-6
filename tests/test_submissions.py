CORRECT = "def add(a, b):\n    return a + b"


def test_wrong_answer_is_recorded_without_rewards(client, catalog):
    headers = catalog["headers"]
    response = client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": "def add(a, b):\n    return a - b"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["submission"]["status"] == "WRONG_ANSWER"
    assert body["first_completion"] is False
    assert body["rewards"] == {"xp": 0, "coins": 0}
    assert body["lesson_completed"] is False
    assert body["user"]["xp"] == 0
    assert body["user"]["coins"] == 0


def test_accepted_answer_grants_rewards_once(client, catalog):
    headers = catalog["headers"]

    first = client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": "\n" + CORRECT + "   \n\n"},
        headers=headers,
    )
    assert first.status_code == 201
    body = first.json()
    assert body["submission"]["status"] == "ACCEPTED"
    assert body["first_completion"] is True
    assert body["rewards"] == {"xp": 10, "coins": 2}
    assert body["user"]["xp"] == 10
    assert body["user"]["coins"] == 2
    assert body["user"]["level"] == 1

    second = client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": CORRECT.replace("\n", "\r\n")},
        headers=headers,
    )
    assert second.status_code == 201
    again = second.json()
    assert again["submission"]["status"] == "ACCEPTED"
    assert again["first_completion"] is False
    assert again["rewards"] == {"xp": 0, "coins": 0}
    assert again["user"]["xp"] == 10

    history = client.get("/api/submissions", headers=headers)
    assert history.status_code == 200
    assert [item["status"] for item in history.json()["submissions"]] == [
        "ACCEPTED",
        "ACCEPTED",
    ]


def test_submission_is_private_to_its_author(client, catalog, register):
    headers = catalog["headers"]
    response = client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": CORRECT},
        headers=headers,
    )
    submission_id = response.json()["submission"]["id"]

    mine = client.get(f"/api/submissions/{submission_id}", headers=headers)
    assert mine.status_code == 200
    assert mine.json()["id"] == submission_id

    other_headers, _user = register("bob")
    hidden = client.get(f"/api/submissions/{submission_id}", headers=other_headers)
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "SUBMISSION_NOT_FOUND"
    assert client.get("/api/submissions", headers=other_headers).json()["submissions"] == []


def test_unpublished_problem_cannot_be_submitted(client, catalog):
    headers = catalog["headers"]
    client.patch(
        f"/api/problems/{catalog['problem']['id']}",
        json={"is_published": False},
        headers=headers,
    )
    response = client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": CORRECT},
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROBLEM_NOT_FOUND"


def test_submission_validation_and_authentication(client, catalog):
    empty = client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": ""},
        headers=catalog["headers"],
    )
    assert empty.status_code == 422

    anonymous = client.post(
        f"/api/problems/{catalog['problem']['id']}/submit",
        json={"answer": CORRECT},
    )
    assert anonymous.status_code == 401
