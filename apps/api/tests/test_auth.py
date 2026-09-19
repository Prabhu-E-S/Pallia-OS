"""Phase 2 authentication tests.

Covers login, generic failure messages, status gating, refresh rotation,
logout + session revocation and rate limiting.
"""


def _login(client, db, tenants, email="login@alpha.pallia.dev", password="c0rrect-h0rse"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_login_success_returns_tokens(client, db, tenants):
    response = _login(client, db, tenants)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] > 0
    assert body["user"]["email"] == "login@alpha.pallia.dev"
    assert "patient.read" in body["user"]["permissions"]
    assert body["user"]["status"] == "ACTIVE"
    assert "pallia_refresh" in response.headers.get("set-cookie", "")


def test_login_access_token_works_with_me(client, db, tenants):
    body = _login(client, db, tenants).json()
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "login@alpha.pallia.dev"


def test_login_wrong_password_is_generic(client, db, tenants):
    response = _login(client, db, tenants, password="wrong-password")
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "UNAUTHORIZED"
    assert error["message"] == "Invalid email or password"


def test_login_unknown_email_is_generic(client, db, tenants):
    response = _login(client, db, tenants, email="nobody@nowhere.dev")
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


def test_login_inactive_user_rejected(client, db, tenants):
    response = _login(client, db, tenants, email="inactive@alpha.pallia.dev")
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


def test_login_suspended_user_rejected(client, db, tenants):
    response = _login(client, db, tenants, email="suspended@alpha.pallia.dev")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_refresh_rotates_token(client, db, tenants):
    login = _login(client, db, tenants)
    refresh_1 = login.json()["refresh_token"]

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert rotated.status_code == 200, rotated.text
    body = rotated.json()
    assert body["access_token"]
    assert body["refresh_token"] != refresh_1

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200

    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert replay.status_code == 401


def test_refresh_from_cookie(client, db, tenants):
    _login(client, db, tenants)
    rotated = client.post("/api/v1/auth/refresh")
    assert rotated.status_code == 200, rotated.text


def test_refresh_without_token_401(client, db, tenants):
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_logout_revokes_session(client, db, tenants):
    login = _login(client, db, tenants)
    access = login.json()["access_token"]
    refresh = login.json()["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert logout.status_code == 200
    assert logout.json()["ok"] is True

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert me.status_code == 401

    refresh_after_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert refresh_after_logout.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_rate_limited(client, db, tenants):
    for _ in range(10):
        response = _login(
            client, db, tenants, email="ratelimit@alpha.pallia.dev", password="wrong-password"
        )
        assert response.status_code == 401

    response = _login(
        client, db, tenants, email="ratelimit@alpha.pallia.dev", password="wrong-password"
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
