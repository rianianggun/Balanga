"""Iteration 4 - Setup verification: login for 4 roles + protected endpoint."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://ririn-balanga.preview.emergentagent.com").rstrip("/")

CREDS = [
    ("admin@ririn.go.id", "Admin123!", "admin"),
    ("verifikator@kalteng.go.id", "Verif123!", "verifikator"),
    ("penilai@kalteng.go.id", "Nilai123!", "penilai"),
    ("perangkat@kalteng.go.id", "Kerja123!", "perangkat"),
]


@pytest.mark.parametrize("email,password,role", CREDS)
def test_login_returns_token_and_role(email, password, role):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("role") == role
    assert isinstance(data.get("token"), str) and len(data["token"]) > 20
    assert data.get("email") == email


@pytest.mark.parametrize("email,password,role", CREDS)
def test_authenticated_me(email, password, role):
    login = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": email, "password": password}, timeout=15).json()
    token = login["token"]
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code == 200, f"/api/auth/me failed for {email}: {r.status_code} {r.text}"
    me = r.json()
    assert me.get("email") == email
    assert me.get("role") == role


def test_me_without_token_rejected():
    r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code in (401, 403)
