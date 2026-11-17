def test_register_login_and_private_profile(client, register):
    headers, user = register("alice")
    assert user["nickname"] == "alice"
    assert user["xp"] == 0 and user["level"] == 1

    me = client.get("/api/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"

    public = client.get(f"/api/users/{user['id']}")
    assert public.status_code == 200
    assert "email" not in public.json()

    login = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "Passw0rd!"},
    )
    assert login.status_code == 200
    assert login.json()["token"]


def test_duplicate_registration_is_a_conflict(client, register):
    register("alice")
    duplicate = client.post(
        "/api/auth/register",
        json={"email": "ALICE@example.com", "password": "Passw0rd!", "nickname": "other"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_TAKEN"

    duplicate_nickname = client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "Passw0rd!", "nickname": "alice"},
    )
    assert duplicate_nickname.status_code == 409
    assert duplicate_nickname.json()["error"]["code"] == "NICKNAME_TAKEN"


def test_validation_and_authentication_errors(client, register):
    invalid = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "short", "nickname": "a!"},
    )
    assert invalid.status_code == 422

    wrong_password = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )
    assert wrong_password.status_code == 401

    missing_token = client.get("/api/users/me")
    assert missing_token.status_code == 401


def test_logout_revokes_the_session(client, register):
    headers, _user = register("alice")
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/users/me", headers=headers).status_code == 401
