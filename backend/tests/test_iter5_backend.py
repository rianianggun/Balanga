"""Iteration 5 backend tests: verify flow, surat PDF, indicators+scores, scoring, AI, reports, stats."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://ririn-balanga.preview.emergentagent.com").rstrip("/")
API = BASE_URL + "/api"

CREDS = {
    "admin": ("admin@ririn.go.id", "Admin123!"),
    "verifikator": ("verifikator@kalteng.go.id", "Verif123!"),
    "verifikator_kapuas": ("verifikator.kapuas@kalteng.go.id", "Verif123!"),
    "penilai": ("penilai@kalteng.go.id", "Nilai123!"),
    "perangkat": ("perangkat@kalteng.go.id", "Kerja123!"),
}


def _login(email, pw):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def tokens():
    return {k: _login(e, p) for k, (e, p) in CREDS.items()}


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- Verifikator: list + verify (ack) ----------
@pytest.fixture(scope="module")
def verifikator_submissions(tokens):
    r = requests.get(f"{API}/submissions", headers=H(tokens["verifikator"]), timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


def test_verifikator_sees_menunggu_verifikasi(verifikator_submissions):
    statuses = {s["status"] for s in verifikator_submissions}
    assert "menunggu_verifikasi" in statuses, f"statuses seen: {statuses}"


def test_verify_requires_acknowledged(tokens, verifikator_submissions):
    pending = [s for s in verifikator_submissions if s["status"] == "menunggu_verifikasi"]
    if not pending:
        pytest.skip("no pending verifikasi (may have been consumed by earlier test run)")
    sid = pending[0]["id"]
    r = requests.post(f"{API}/submissions/{sid}/verify",
                      json={"action": "approve", "acknowledged": False},
                      headers=H(tokens["verifikator"]), timeout=15)
    assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text}"


def test_verify_approve_with_ack(tokens, verifikator_submissions):
    pending = [s for s in verifikator_submissions if s["status"] == "menunggu_verifikasi"]
    if not pending:
        pytest.skip("no pending verifikasi")
    sid = pending[0]["id"]
    r = requests.post(f"{API}/submissions/{sid}/verify",
                      json={"action": "approve", "acknowledged": True, "notes": "OK"},
                      headers=H(tokens["verifikator"]), timeout=15)
    assert r.status_code == 200, r.text
    r2 = requests.get(f"{API}/submissions/{sid}", headers=H(tokens["verifikator"]), timeout=15)
    assert r2.status_code == 200
    s = r2.json()
    assert s["status"] == "menunggu_penilaian"
    assert s["verification"]["acknowledged"] is True
    # stash for downstream tests
    pytest.approved_sid = sid


# ---------- Surat verifikasi PDF ----------
def test_surat_verifikasi_pdf(tokens):
    sid = getattr(pytest, "approved_sid", None)
    if not sid:
        # find any menunggu_penilaian or selesai
        r = requests.get(f"{API}/submissions", headers=H(tokens["verifikator"]), timeout=15).json()
        cand = [s for s in r if s["status"] in ("menunggu_penilaian", "selesai")]
        if not cand:
            pytest.skip("no verified submission available")
        sid = cand[0]["id"]
    r = requests.get(f"{API}/submissions/{sid}/surat-verifikasi",
                     params={"auth": tokens["verifikator"]}, timeout=30)
    assert r.status_code == 200, r.text
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content.startswith(b"%PDF"), "PDF body doesn't start with %PDF"
    assert len(r.content) > 500


def test_surat_verifikasi_wrong_area_forbidden(tokens):
    # kapuas verifikator should not see palangka raya sid
    sid = getattr(pytest, "approved_sid", None)
    if not sid:
        pytest.skip("no approved sid")
    r = requests.get(f"{API}/submissions/{sid}/surat-verifikasi",
                     params={"auth": tokens["verifikator_kapuas"]}, timeout=15)
    assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"


def test_surat_verifikasi_rejects_unverified(tokens):
    # pick a draft or menunggu_verifikasi submission
    r = requests.get(f"{API}/submissions", headers=H(tokens["verifikator"]), timeout=15).json()
    unver = [s for s in r if s["status"] == "menunggu_verifikasi"]
    if not unver:
        # get perangkat's own draft
        r2 = requests.get(f"{API}/submissions", headers=H(tokens["perangkat"]), timeout=15).json()
        unver = [s for s in r2 if s["status"] in ("draft", "menunggu_verifikasi", "ditolak")]
    if not unver:
        pytest.skip("no unverified submission")
    sid = unver[0]["id"]
    r = requests.get(f"{API}/submissions/{sid}/surat-verifikasi",
                     params={"auth": tokens["verifikator"]}, timeout=15)
    assert r.status_code == 400, f"expected 400 got {r.status_code}"


# ---------- Indicators ----------
def test_indicators_umum_has_scores(tokens):
    r = requests.get(f"{API}/indicators", params={"type": "umum"},
                     headers=H(tokens["penilai"]), timeout=15)
    assert r.status_code == 200
    umum = r.json()
    assert len(umum) == 3, f"expected 3 umum, got {len(umum)}"
    for u in umum:
        assert isinstance(u.get("scores"), list) and len(u["scores"]) == 5, f"scores: {u.get('scores')}"
    # per task spec
    sc = sorted([tuple(u["scores"]) for u in umum])
    assert (10, 20, 30, 40, 50) in sc
    assert (20, 40, 60, 80, 100) in sc


def test_indicators_for_submission_teknis_scores(tokens):
    r = requests.get(f"{API}/indicators/for-submission",
                     params={"level": "kabupaten", "urusan": "Bidang Pendidikan"},
                     headers=H(tokens["penilai"]), timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert len(data["teknis"]) >= 1
    for t in data["teknis"]:
        assert t.get("scores") and len(t["scores"]) == 5, f"teknis scores missing: {t.get('name')}={t.get('scores')}"


# ---------- Penilai scoring ----------
@pytest.fixture(scope="module")
def scorable_submission(tokens):
    r = requests.get(f"{API}/submissions", headers=H(tokens["penilai"]), timeout=15).json()
    pend = [s for s in r if s["status"] == "menunggu_penilaian"]
    if not pend:
        pytest.skip("no scorable submission")
    return pend[0]


def test_score_submission_kelas_e(tokens, scorable_submission):
    s = scorable_submission
    r = requests.get(f"{API}/indicators/for-submission",
                     params={"level": s["level"], "urusan": s["urusan"], **({"sub_urusan": s["sub_urusan"]} if s.get("sub_urusan") else {})},
                     headers=H(tokens["penilai"]), timeout=15)
    assert r.status_code == 200
    inds = r.json()
    all_inds = inds["umum"] + inds["teknis"]
    items = [{"indicator_id": i["id"], "score": i["scores"][4], "kelas": "e"} for i in all_inds]
    r = requests.post(f"{API}/submissions/{s['id']}/score",
                      json={"items": items, "overall_note": "TEST_"},
                      headers=H(tokens["penilai"]), timeout=30)
    assert r.status_code == 200, r.text
    sc = r.json()["scoring"]
    assert sc["umum_total"] == sum(i["scores"][4] for i in inds["umum"])
    assert sc["teknis_total"] == sum(i["scores"][4] for i in inds["teknis"])
    assert sc["total"] == round(sc["umum_total"] + sc["teknis_total"], 2)
    pytest.scored_sid = s["id"]


def test_score_rejects_invalid_score(tokens):
    # need a menunggu_penilaian submission — check if any left
    r = requests.get(f"{API}/submissions", headers=H(tokens["penilai"]), timeout=15).json()
    pend = [s for s in r if s["status"] == "menunggu_penilaian"]
    if not pend:
        pytest.skip("no scorable submission left")
    s = pend[0]
    r = requests.get(f"{API}/indicators/for-submission",
                     params={"level": s["level"], "urusan": s["urusan"], **({"sub_urusan": s["sub_urusan"]} if s.get("sub_urusan") else {})},
                     headers=H(tokens["penilai"]), timeout=15).json()
    all_inds = r["umum"] + r["teknis"]
    # use a value not in scores series (e.g., 7)
    items = [{"indicator_id": i["id"], "score": 7, "kelas": "a"} for i in all_inds]
    r2 = requests.post(f"{API}/submissions/{s['id']}/score",
                       json={"items": items}, headers=H(tokens["penilai"]), timeout=15)
    assert r2.status_code == 400, f"expected 400, got {r2.status_code} {r2.text}"


# ---------- Reports & Stats ----------
def test_reports_preview_combined(tokens):
    r = requests.get(f"{API}/reports/preview",
                     params={"area": "Kota Palangka Raya", "device_name": "Dinas Pendidikan Kota Palangka Raya"},
                     headers=H(tokens["penilai"]), timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["rows"]) >= 1
    for row in data["rows"]:
        for k in ("umum_total", "teknis_total", "total", "final", "tipe"):
            assert k in row, f"missing {k} in row"
    if len(data["rows"]) >= 2:
        assert data["combined"] is not None
        assert data["combined"]["tipe"]["key"] in ("A", "B")


def test_reports_preview_multiplier(tokens):
    r = requests.get(f"{API}/reports/preview",
                     params={"area": "Kota Palangka Raya",
                             "device_name": "Dinas Pendidikan Kota Palangka Raya",
                             "apply_multiplier": "true"},
                     headers=H(tokens["penilai"]), timeout=15).json()
    for row in r["rows"]:
        assert row["final"] == round(row["total"] * 1.1, 2), f"final mismatch: {row}"


def test_stats_by_area_nonempty(tokens):
    r = requests.get(f"{API}/stats/by-area", headers=H(tokens["penilai"]), timeout=15)
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_stats_yearly_nonempty(tokens):
    r = requests.get(f"{API}/stats/yearly", headers=H(tokens["admin"]), timeout=15)
    assert r.status_code == 200
    assert len(r.json()) > 0


# ---------- AI recommend (ONLY ONCE) ----------
def test_ai_recommend_once(tokens):
    r = requests.get(f"{API}/submissions", headers=H(tokens["penilai"]), timeout=15).json()
    pend = [s for s in r if s["status"] == "menunggu_penilaian"]
    if not pend:
        pytest.skip("no menunggu_penilaian for AI")
    sid = pend[0]["id"]
    r = requests.post(f"{API}/submissions/{sid}/ai-recommend",
                      headers=H(tokens["penilai"]), timeout=120)
    assert r.status_code == 200, f"AI failed: {r.status_code} {r.text[:500]}"
    data = r.json()
    assert "items" in data and isinstance(data["items"], list)
    for it in data["items"]:
        assert "indicator_id" in it
        assert "kelas" in it  # a-e or null
        assert "score" in it
        assert "reason" in it
    # verify persistence
    r2 = requests.get(f"{API}/submissions/{sid}", headers=H(tokens["penilai"]), timeout=15).json()
    assert r2.get("ai_recommendation") is not None
