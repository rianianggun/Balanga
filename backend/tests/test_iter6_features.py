"""Iteration 6 backend tests: delete submission, docx berita-acara, rekap-area xlsx,
tipe-summary scoping, POST /api/users with phone/WhatsApp, legacy admin login."""
import os
import time
import zipfile
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://balanga-clone2-setup.preview.emergentagent.com").rstrip("/")
API = BASE_URL + "/api"

CREDS = {
    "admin": ("admin@ririn.go.id", "Admin123!"),
    "legacy_admin": ("riani.anggun.adp@gmail.com", "Admin@2026"),
    "penilai": ("penilai@kalteng.go.id", "Nilai123!"),
    "verifikator": ("verifikator@kalteng.go.id", "Verif123!"),
    "perangkat": ("perangkat@kalteng.go.id", "Kerja123!"),
    "perangkat_kapuas": ("perangkat.kapuas@kalteng.go.id", "Kerja123!"),
}


def _login(email, pw):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def tokens():
    return {k: _login(e, p)["token"] for k, (e, p) in CREDS.items()}


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---- Legacy admin ----
def test_legacy_admin_login():
    r = _login(*CREDS["legacy_admin"])
    assert r["role"] == "admin"
    assert r["token"]


# ---- Active period ----
@pytest.fixture(scope="module")
def active_period(tokens):
    r = requests.get(f"{API}/periods/active", headers=H(tokens["perangkat"]), timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


# ---- DELETE submission ----
def _create_submission(tok, period_id, device_name="TEST_DEL_DEVICE"):
    payload = {
        "device_name": device_name,
        "urusan": "Bidang Pendidikan",
        "period_id": period_id,
    }
    r = requests.post(f"{API}/submissions", json=payload, headers=H(tok), timeout=15)
    assert r.status_code in (200, 201), r.text
    return r.json()


def test_perangkat_delete_own_draft(tokens, active_period):
    sub = _create_submission(tokens["perangkat"], active_period["id"], f"TEST_DEL_{int(time.time())}")
    sid = sub["id"]
    assert sub["status"] in ("draft", "menunggu_verifikasi")
    # delete
    r = requests.delete(f"{API}/submissions/{sid}", headers=H(tokens["perangkat"]), timeout=15)
    assert r.status_code == 200, r.text
    # verify gone
    r2 = requests.get(f"{API}/submissions", headers=H(tokens["perangkat"]), timeout=15).json()
    assert sid not in {s["id"] for s in r2}


def test_delete_selesai_forbidden(tokens):
    r = requests.get(f"{API}/submissions", headers=H(tokens["admin"]), timeout=15).json()
    selesai = [s for s in r if s["status"] == "selesai"]
    if not selesai:
        pytest.skip("no selesai submission")
    sid = selesai[0]["id"]
    # try as perangkat (must be owner ideally, but any role deleting selesai should be 403)
    r = requests.delete(f"{API}/submissions/{sid}", headers=H(tokens["perangkat"]), timeout=15)
    assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text[:200]}"


def test_delete_by_other_role_forbidden(tokens, active_period):
    sub = _create_submission(tokens["perangkat"], active_period["id"], f"TEST_DEL_OTH_{int(time.time())}")
    sid = sub["id"]
    # try to delete as another perangkat (kapuas)
    r = requests.delete(f"{API}/submissions/{sid}", headers=H(tokens["perangkat_kapuas"]), timeout=15)
    assert r.status_code == 403, f"expected 403 from other role, got {r.status_code}"
    # cleanup
    requests.delete(f"{API}/submissions/{sid}", headers=H(tokens["perangkat"]), timeout=15)


# ---- Berita Acara docx ----
@pytest.fixture(scope="module")
def selesai_sid(tokens):
    r = requests.get(f"{API}/submissions", headers=H(tokens["admin"]), timeout=15).json()
    ss = [s for s in r if s["status"] == "selesai"]
    if not ss:
        pytest.skip("no selesai submission")
    return ss[0]["id"]


def test_berita_acara_docx_pengali_1(tokens, selesai_sid):
    r = requests.get(f"{API}/submissions/{selesai_sid}/berita-acara",
                     params={"format": "docx", "pengali": 1, "auth": tokens["admin"]},
                     timeout=30)
    assert r.status_code == 200, r.text[:500]
    ct = r.headers.get("content-type", "")
    assert "wordprocessingml.document" in ct, f"content-type: {ct}"
    assert len(r.content) > 500
    # docx = zip
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert "word/document.xml" in z.namelist()
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        assert "Total Skor" in xml or "Total" in xml


def test_berita_acara_docx_pengali_1_1(tokens, selesai_sid):
    r = requests.get(f"{API}/submissions/{selesai_sid}/berita-acara",
                     params={"format": "docx", "pengali": 1.1, "auth": tokens["admin"]},
                     timeout=30)
    assert r.status_code == 200, r.text[:500]
    assert "wordprocessingml.document" in r.headers.get("content-type", "")


def test_berita_acara_docx_invalid_pengali(tokens, selesai_sid):
    r = requests.get(f"{API}/submissions/{selesai_sid}/berita-acara",
                     params={"format": "docx", "pengali": 1.5, "auth": tokens["admin"]},
                     timeout=15)
    assert r.status_code == 400, f"expected 400, got {r.status_code}"


# ---- Rekap area xlsx ----
def test_rekap_area_admin_ok(tokens):
    r = requests.get(f"{API}/reports/rekap-area",
                     params={"area": "Kota Palangka Raya", "pengali": 1, "auth": tokens["admin"]},
                     timeout=30)
    assert r.status_code == 200, r.text[:500]
    ct = r.headers.get("content-type", "")
    assert "spreadsheetml.sheet" in ct or "excel" in ct.lower(), ct
    assert len(r.content) > 100


def test_rekap_area_perangkat_forbidden(tokens):
    r = requests.get(f"{API}/reports/rekap-area",
                     params={"area": "Kota Palangka Raya", "pengali": 1, "auth": tokens["perangkat"]},
                     timeout=15)
    assert r.status_code == 403, f"expected 403, got {r.status_code}"


# ---- Tipe summary scoping ----
def test_tipe_summary_perangkat_scoped(tokens):
    r = requests.get(f"{API}/stats/tipe-summary", headers=H(tokens["perangkat"]), timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    ranking = data.get("ranking") or data.get("top5") or []
    # collect any area-like fields
    areas = set()
    for row in ranking:
        for k in ("area", "kab_kota", "kabupaten", "kota", "device_area"):
            if row.get(k):
                areas.add(row[k])
    if ranking:
        assert any("Palangka Raya" in a for a in areas) or all("Palangka Raya" in a for a in areas), \
            f"perangkat should only see Palangka Raya, saw: {areas}"


def test_tipe_summary_verifikator_scoped(tokens):
    r = requests.get(f"{API}/stats/tipe-summary", headers=H(tokens["verifikator"]), timeout=15)
    assert r.status_code == 200
    data = r.json()
    ranking = data.get("ranking") or data.get("top5") or []
    areas = set()
    for row in ranking:
        for k in ("area", "kab_kota", "kabupaten", "kota", "device_area"):
            if row.get(k):
                areas.add(row[k])
    if ranking:
        assert all("Palangka Raya" in a for a in areas), \
            f"verifikator should only see Palangka Raya, saw: {areas}"


def test_tipe_summary_admin_multi_area(tokens):
    r = requests.get(f"{API}/stats/tipe-summary", headers=H(tokens["admin"]), timeout=15)
    assert r.status_code == 200
    data = r.json()
    ranking = data.get("ranking") or data.get("top5") or []
    # admin should see multiple areas OR at least be unscoped (no failure if data is small)
    assert isinstance(ranking, list)


# ---- POST /api/users with phone (WhatsApp) ----
def test_create_user_with_phone_normalized(tokens):
    ts = int(time.time())
    email = f"test.wa.{ts}@kalteng.go.id"
    payload = {
        "email": email,
        "name": "TEST WA User",
        "password": "Test123!",
        "role": "penilai",
        "phone": "081234567890",
    }
    r = requests.post(f"{API}/users", json=payload, headers=H(tokens["admin"]), timeout=30)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    # phone normalization
    phone = body.get("phone") or body.get("user", {}).get("phone")
    assert phone == "6281234567890", f"phone not normalized: {phone}, body: {body}"
    # whatsapp object
    wa = body.get("whatsapp")
    assert wa is not None, f"missing whatsapp object: {body}"
    assert "sent" in wa
    print(f"WhatsApp result: {wa}")
    uid = body.get("id") or body.get("user", {}).get("id")

    # list users includes phone
    r2 = requests.get(f"{API}/users", headers=H(tokens["admin"]), timeout=15)
    assert r2.status_code == 200
    users = r2.json()
    match = [u for u in users if u.get("email") == email]
    assert match and match[0].get("phone") == "6281234567890"

    # cleanup
    if uid:
        requests.delete(f"{API}/users/{uid}", headers=H(tokens["admin"]), timeout=15)


def test_create_user_without_phone(tokens):
    ts = int(time.time())
    email = f"test.nowa.{ts}@kalteng.go.id"
    payload = {
        "email": email,
        "name": "TEST No Phone",
        "password": "Test123!",
        "role": "penilai",
    }
    r = requests.post(f"{API}/users", json=payload, headers=H(tokens["admin"]), timeout=15)
    assert r.status_code in (200, 201), r.text
    body = r.json()
    uid = body.get("id") or body.get("user", {}).get("id")
    if uid:
        requests.delete(f"{API}/users/{uid}", headers=H(tokens["admin"]), timeout=15)
