import json
from conftest import login


"""
home route is protected by @login_required
unauthenticated users should be redirected to the login page
"""
def test_home_redirects_when_not_logged_in(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 401) # redirects to /login


# valid credentials create a logged-in session and return the home page
def test_login_works(client):
    r = login(client, "user@test.com", "userpass")
    assert r.status_code == 200
    assert b"Library" in r.data  # basic check that some expected content exists


# non-admin users must be forbidden from /admin/* routes
def test_non_admin_blocked_from_admin_users(client):
    login(client, "user@test.com", "userpass")
    r = client.get("/admin/users")
    assert r.status_code == 403


# admin users should be allowed to access /admin/users
def test_admin_can_access_admin_users(client):
    login(client, "admin@test.com", "adminpass")
    r = client.get("/admin/users")
    assert r.status_code == 200


# /ai-chat should always return JSON with a 'reply' key when called correctly
def test_ai_chat_returns_json(client):
    login(client, "user@test.com", "userpass")
    payload = {"message": "What books am I reading?"}
    r = client.post("/ai-chat", data=json.dumps(payload), content_type="application/json")
    assert r.status_code == 200
    data = r.get_json()
    assert "reply" in data
