def test_comments_are_public_and_persisted(client, catalog):
    headers = catalog["headers"]
    problem_id = catalog["problem"]["id"]

    created = client.post(
        f"/api/problems/{problem_id}/comments",
        json={"body": "  Use a helper function.  "},
        headers=headers,
    )
    assert created.status_code == 201
    comment = created.json()
    assert comment["body"] == "Use a helper function."
    assert comment["problem_id"] == problem_id
    assert comment["updated_at"] is None

    public = client.get(f"/api/problems/{problem_id}/comments")
    assert public.status_code == 200
    assert [item["id"] for item in public.json()["comments"]] == [comment["id"]]


def test_blank_comment_is_rejected(client, catalog):
    response = client.post(
        f"/api/problems/{catalog['problem']['id']}/comments",
        json={"body": "   "},
        headers=catalog["headers"],
    )
    assert response.status_code == 422


def test_only_author_can_edit_or_delete(client, catalog, register):
    headers = catalog["headers"]
    problem_id = catalog["problem"]["id"]
    comment = client.post(
        f"/api/problems/{problem_id}/comments",
        json={"body": "first draft"},
        headers=headers,
    ).json()

    updated = client.patch(
        f"/api/comments/{comment['id']}",
        json={"body": "final draft"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["body"] == "final draft"
    assert updated.json()["updated_at"] is not None

    other_headers, _user = register("bob")
    forbidden = client.patch(
        f"/api/comments/{comment['id']}",
        json={"body": "hijacked"},
        headers=other_headers,
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "COMMENT_FORBIDDEN"

    blocked_delete = client.delete(f"/api/comments/{comment['id']}", headers=other_headers)
    assert blocked_delete.status_code == 403

    removed = client.delete(f"/api/comments/{comment['id']}", headers=headers)
    assert removed.status_code == 204
    assert client.get(f"/api/problems/{problem_id}/comments").json()["comments"] == []


def test_missing_comment_and_authentication(client, catalog):
    assert client.get("/api/problems/999999/comments").status_code == 404
    missing = client.delete("/api/comments/999999", headers=catalog["headers"])
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "COMMENT_NOT_FOUND"
    assert (
        client.post(
            f"/api/problems/{catalog['problem']['id']}/comments",
            json={"body": "anonymous"},
        ).status_code
        == 401
    )
