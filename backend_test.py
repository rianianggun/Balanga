#!/usr/bin/env python3
"""
Backend API Testing for Balanga (Si-Scoring Kalteng)
Tests notifications, berita-acara, reports, stats, file downloads
"""

import requests
import json
import io
import time
from typing import Dict, Optional

# Read backend URL from frontend/.env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BASE_URL = line.split('=', 1)[1].strip()
            break

API_URL = f"{BASE_URL}/api"

# Test credentials
CREDENTIALS = {
    "admin": {"email": "admin@ririn.go.id", "password": "Admin123!"},
    "penilai": {"email": "penilai@kalteng.go.id", "password": "Nilai123!"},
    "verifikator": {"email": "verifikator@kalteng.go.id", "password": "Verif123!"},
    "perangkat": {"email": "perangkat@kalteng.go.id", "password": "Kerja123!"}
}

class TestSession:
    def __init__(self):
        self.tokens = {}
        self.users = {}
        self.results = []
        
    def log(self, test_name: str, passed: bool, message: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({"test": test_name, "passed": passed, "message": message})
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
    
    def login(self, role: str) -> Optional[str]:
        """Login and return token"""
        try:
            resp = requests.post(f"{API_URL}/auth/login", json=CREDENTIALS[role], timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("token")
                self.tokens[role] = token
                self.users[role] = data
                return token
            else:
                self.log(f"Login {role}", False, f"Status {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            self.log(f"Login {role}", False, f"Exception: {str(e)}")
            return None
    
    def get(self, endpoint: str, token: str = None, params: dict = None) -> requests.Response:
        """GET request with optional auth"""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return requests.get(f"{API_URL}{endpoint}", headers=headers, params=params, timeout=30)
    
    def post(self, endpoint: str, token: str = None, json_data: dict = None, files: dict = None, data: dict = None) -> requests.Response:
        """POST request with optional auth"""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return requests.post(f"{API_URL}{endpoint}", headers=headers, json=json_data, files=files, data=data, timeout=30)

def test_regression(session: TestSession):
    """Test basic functionality: login, /me, submissions for all roles"""
    print("\n=== REGRESSION TESTS ===")
    
    # Test login for all 4 roles
    for role in ["admin", "penilai", "verifikator", "perangkat"]:
        token = session.login(role)
        session.log(f"Login {role}", token is not None)
        
        if token:
            # Test /auth/me
            resp = session.get("/auth/me", token)
            session.log(f"GET /auth/me ({role})", resp.status_code == 200, 
                       f"Status: {resp.status_code}")
            
            # Test GET /submissions
            resp = session.get("/submissions", token)
            session.log(f"GET /submissions ({role})", resp.status_code == 200,
                       f"Status: {resp.status_code}, Count: {len(resp.json()) if resp.status_code == 200 else 0}")

def test_notifications(session: TestSession):
    """Test notification endpoints"""
    print("\n=== NOTIFICATION TESTS ===")
    
    # Test GET /notifications for perangkat
    token = session.tokens.get("perangkat")
    if not token:
        session.log("GET /notifications", False, "No perangkat token")
        return
    
    resp = session.get("/notifications", token)
    if resp.status_code == 200:
        data = resp.json()
        session.log("GET /notifications", True, f"Received {len(data)} notifications")
        
        # Check structure
        has_event = any(n.get("kind") == "event" for n in data)
        has_period = any(n.get("kind") == "period" for n in data)
        session.log("Notifications have event items", has_event)
        session.log("Notifications have period items", has_period)
        
        # Check required fields
        if data:
            first = data[0]
            has_fields = all(k in first for k in ["id", "kind", "level", "message", "read"])
            session.log("Notification structure valid", has_fields, 
                       f"Fields: {list(first.keys())}")
    else:
        session.log("GET /notifications", False, f"Status {resp.status_code}: {resp.text[:200]}")
    
    # Test POST /notifications/read-all
    resp = session.post("/notifications/read-all", token)
    session.log("POST /notifications/read-all", resp.status_code == 200,
               f"Status: {resp.status_code}")
    
    # Verify all event notifications are now read
    if resp.status_code == 200:
        resp = session.get("/notifications", token)
        if resp.status_code == 200:
            data = resp.json()
            event_items = [n for n in data if n.get("kind") == "event"]
            all_read = all(n.get("read") == True for n in event_items)
            session.log("All event notifications marked read", all_read,
                       f"Event items: {len(event_items)}, All read: {all_read}")

def test_notification_flow(session: TestSession):
    """Test full flow to trigger notifications"""
    print("\n=== NOTIFICATION FLOW TEST ===")
    
    perangkat_token = session.tokens.get("perangkat")
    verifikator_token = session.tokens.get("verifikator")
    penilai_token = session.tokens.get("penilai")
    
    if not all([perangkat_token, verifikator_token, penilai_token]):
        session.log("Notification flow", False, "Missing required tokens")
        return
    
    # Get active period
    resp = session.get("/periods/active", perangkat_token)
    if resp.status_code != 200:
        session.log("Get active period", False, f"Status {resp.status_code}")
        return
    
    period = resp.json()
    period_id = period.get("id")
    session.log("Get active period", True, f"Period: {period.get('name')}")
    
    # Create submission
    submission_data = {
        "device_name": "Dinas Uji Backend",
        "urusan": "Bidang Kebudayaan",
        "sub_urusan": None,
        "period_id": period_id
    }
    resp = session.post("/submissions", perangkat_token, json_data=submission_data)
    if resp.status_code != 200:
        session.log("Create submission", False, f"Status {resp.status_code}: {resp.text[:200]}")
        return
    
    submission = resp.json()
    sid = submission.get("id")
    session.log("Create submission", True, f"ID: {sid}")
    
    # Get indicators
    resp = session.get("/indicators/for-submission", perangkat_token, 
                      params={"level": "kabupaten", "urusan": "Bidang Kebudayaan"})
    if resp.status_code != 200:
        session.log("Get indicators", False, f"Status {resp.status_code}")
        return
    
    indicators_data = resp.json()
    umum = indicators_data.get("umum", [])
    teknis = indicators_data.get("teknis", [])
    all_indicators = umum + teknis
    session.log("Get indicators", True, f"Umum: {len(umum)}, Teknis: {len(teknis)}")
    
    # Upload files for all indicators
    # Note: This may fail if object storage is not available
    upload_success = True
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000317 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n410\n%%EOF"
    
    for indicator in all_indicators[:3]:  # Upload for first 3 indicators to save time
        indicator_id = indicator.get("id")
        files = {"file": ("bukti.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {"indicator_id": indicator_id}
        
        resp = session.post(f"/submissions/{sid}/upload", perangkat_token, files=files, data=data)
        if resp.status_code not in [200, 500, 503]:
            upload_success = False
            session.log(f"Upload indicator {indicator_id[:8]}", False, 
                       f"Status {resp.status_code}: {resp.text[:100]}")
            break
        elif resp.status_code in [500, 503]:
            session.log("Upload files", False, 
                       "Object storage error (5xx) - continuing with existing submissions")
            upload_success = False
            break
    
    if upload_success and all_indicators:
        session.log("Upload files", True, f"Uploaded {min(3, len(all_indicators))} files")
        
        # Submit
        resp = session.post(f"/submissions/{sid}/submit", perangkat_token)
        session.log("Submit submission", resp.status_code == 200,
                   f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            # Verify as verifikator
            verify_data = {
                "action": "approve",
                "notes": "ok",
                "acknowledged": True
            }
            resp = session.post(f"/submissions/{sid}/verify", verifikator_token, json_data=verify_data)
            session.log("Verify submission", resp.status_code == 200,
                       f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                # Check perangkat notifications for DIVERIFIKASI
                resp = session.get("/notifications", perangkat_token)
                if resp.status_code == 200:
                    notifications = resp.json()
                    has_verified = any("DIVERIFIKASI" in n.get("message", "") for n in notifications)
                    session.log("Notification: DIVERIFIKASI", has_verified,
                               f"Found in {len(notifications)} notifications")
                
                # Score as penilai
                # Get submission to build score items
                resp = session.get(f"/submissions/{sid}", penilai_token)
                if resp.status_code == 200:
                    sub = resp.json()
                    
                    # Build score items
                    score_items = []
                    for ind in all_indicators:
                        scores = ind.get("scores")
                        if scores and len(scores) > 0:
                            score = scores[0]  # kelas "a"
                            kelas = "a"
                        else:
                            score = 10
                            kelas = None
                        
                        score_items.append({
                            "indicator_id": ind["id"],
                            "ok": True,
                            "note": "",
                            "data_validasi": "123",
                            "kelas": kelas,
                            "score": score
                        })
                    
                    score_data = {
                        "items": score_items,
                        "overall_note": "uji"
                    }
                    
                    resp = session.post(f"/submissions/{sid}/score", penilai_token, json_data=score_data)
                    session.log("Score submission", resp.status_code == 200,
                               f"Status: {resp.status_code}")
                    
                    if resp.status_code == 200:
                        # Check perangkat notifications for SELESAI
                        time.sleep(0.5)  # Brief delay
                        resp = session.get("/notifications", perangkat_token)
                        if resp.status_code == 200:
                            notifications = resp.json()
                            has_selesai = any("SELESAI" in n.get("message", "") for n in notifications)
                            session.log("Notification: SELESAI", has_selesai,
                                       f"Found in {len(notifications)} notifications")
    else:
        session.log("Notification flow", False, 
                   "Skipping flow test - using existing submissions for other tests")

def test_berita_acara(session: TestSession):
    """Test berita acara endpoint"""
    print("\n=== BERITA ACARA TESTS ===")
    
    penilai_token = session.tokens.get("penilai")
    verifikator_token = session.tokens.get("verifikator")
    perangkat_token = session.tokens.get("perangkat")
    
    if not penilai_token:
        session.log("Berita Acara tests", False, "No penilai token")
        return
    
    # Get a submission with status "selesai"
    resp = session.get("/submissions", penilai_token)
    if resp.status_code != 200:
        session.log("Get submissions", False, f"Status {resp.status_code}")
        return
    
    submissions = resp.json()
    selesai_subs = [s for s in submissions if s.get("status") == "selesai"]
    
    if not selesai_subs:
        session.log("Berita Acara tests", False, "No 'selesai' submissions found")
        return
    
    sid = selesai_subs[0]["id"]
    session.log("Found selesai submission", True, f"ID: {sid[:8]}...")
    
    # Test xlsx format with pengali=1
    resp = session.get(f"/submissions/{sid}/berita-acara", penilai_token,
                      params={"format": "xlsx", "pengali": 1})
    is_xlsx = resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/vnd.openxmlformats")
    has_pk = resp.content[:2] == b'PK' if resp.status_code == 200 else False
    session.log("GET berita-acara format=xlsx pengali=1", is_xlsx and has_pk,
               f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type', '')}, Starts with PK: {has_pk}")
    
    # Test pdf format
    resp = session.get(f"/submissions/{sid}/berita-acara", penilai_token,
                      params={"format": "pdf", "pengali": 1})
    is_pdf = resp.status_code == 200 and resp.headers.get("content-type") == "application/pdf"
    has_pdf_header = resp.content[:4] == b'%PDF' if resp.status_code == 200 else False
    session.log("GET berita-acara format=pdf", is_pdf and has_pdf_header,
               f"Status: {resp.status_code}, Starts with %PDF: {has_pdf_header}")
    
    # Test pengali=2 should return 400
    resp = session.get(f"/submissions/{sid}/berita-acara", penilai_token,
                      params={"format": "xlsx", "pengali": 2})
    session.log("GET berita-acara pengali=2 returns 400", resp.status_code == 400,
               f"Status: {resp.status_code}")
    
    # Test with auth query parameter instead of header
    resp = requests.get(f"{API_URL}/submissions/{sid}/berita-acara",
                       params={"format": "xlsx", "pengali": 1, "auth": penilai_token},
                       timeout=30)
    session.log("GET berita-acara with auth query param", resp.status_code == 200,
               f"Status: {resp.status_code}")
    
    # Test non-selesai submission should return 400
    non_selesai = [s for s in submissions if s.get("status") != "selesai"]
    if non_selesai:
        sid_draft = non_selesai[0]["id"]
        resp = session.get(f"/submissions/{sid_draft}/berita-acara", penilai_token,
                          params={"format": "xlsx", "pengali": 1})
        session.log("GET berita-acara non-selesai returns 400", resp.status_code == 400,
                   f"Status: {resp.status_code}")
    
    # Test verifikator accessing submission from another area should return 403
    # First check if verifikator has area
    if verifikator_token:
        verif_user = session.users.get("verifikator", {})
        verif_area = verif_user.get("area")
        other_area_subs = [s for s in selesai_subs if s.get("area") != verif_area]
        
        if other_area_subs:
            sid_other = other_area_subs[0]["id"]
            resp = session.get(f"/submissions/{sid_other}/berita-acara", verifikator_token,
                              params={"format": "xlsx", "pengali": 1})
            session.log("GET berita-acara verifikator other area returns 403", resp.status_code == 403,
                       f"Status: {resp.status_code}")

def test_reports_rekap(session: TestSession):
    """Test reports/rekap endpoint"""
    print("\n=== REPORTS REKAP TESTS ===")
    
    penilai_token = session.tokens.get("penilai")
    perangkat_token = session.tokens.get("perangkat")
    
    if not penilai_token:
        session.log("Reports rekap tests", False, "No penilai token")
        return
    
    # Test xlsx format
    resp = session.get("/reports/rekap", penilai_token,
                      params={"format": "xlsx", "auth": penilai_token})
    is_xlsx = resp.status_code == 200 and resp.content[:2] == b'PK'
    session.log("GET /reports/rekap format=xlsx", is_xlsx,
               f"Status: {resp.status_code}, Starts with PK: {is_xlsx}")
    
    # Test pdf format with pengali=1.1
    resp = session.get("/reports/rekap", penilai_token,
                      params={"format": "pdf", "pengali": 1.1})
    is_pdf = resp.status_code == 200 and resp.content[:4] == b'%PDF'
    session.log("GET /reports/rekap format=pdf pengali=1.1", is_pdf,
               f"Status: {resp.status_code}, Starts with %PDF: {is_pdf}")
    
    # Test with explicit period_id
    resp = session.get("/periods", penilai_token)
    if resp.status_code == 200:
        periods = resp.json()
        if periods:
            period_id = periods[0]["id"]
            resp = session.get("/reports/rekap", penilai_token,
                              params={"format": "xlsx", "period_id": period_id})
            session.log("GET /reports/rekap with period_id", resp.status_code == 200,
                       f"Status: {resp.status_code}")
    
    # Test perangkat should get 403
    if perangkat_token:
        resp = session.get("/reports/rekap", perangkat_token,
                          params={"format": "xlsx"})
        session.log("GET /reports/rekap as perangkat returns 403", resp.status_code == 403,
                   f"Status: {resp.status_code}")
    
    # Test pengali=1.5 should return 400
    resp = session.get("/reports/rekap", penilai_token,
                      params={"format": "xlsx", "pengali": 1.5})
    session.log("GET /reports/rekap pengali=1.5 returns 400", resp.status_code == 400,
               f"Status: {resp.status_code}")

def test_stats_endpoints(session: TestSession):
    """Test stats endpoints"""
    print("\n=== STATS ENDPOINTS TESTS ===")
    
    penilai_token = session.tokens.get("penilai")
    perangkat_token = session.tokens.get("perangkat")
    admin_token = session.tokens.get("admin")
    verifikator_token = session.tokens.get("verifikator")
    
    # Test /stats/tipe-summary (accessible by penilai and perangkat)
    if penilai_token:
        resp = session.get("/stats/tipe-summary", penilai_token)
        if resp.status_code == 200:
            data = resp.json()
            has_counts = "counts" in data and all(k in data["counts"] for k in ["A", "B", "C", "Lainnya"])
            has_total = "total_devices" in data
            has_ranking = "ranking" in data and isinstance(data["ranking"], list)
            has_pengali = "pengali" in data
            
            # Verify sum(counts) == total_devices == len(ranking)
            counts_sum = sum(data["counts"].values()) if has_counts else 0
            total_devices = data.get("total_devices", 0)
            ranking_len = len(data.get("ranking", []))
            sums_match = counts_sum == total_devices == ranking_len
            
            # Check ranking structure
            ranking_valid = True
            if data.get("ranking"):
                first_rank = data["ranking"][0]
                ranking_valid = all(k in first_rank for k in ["rank", "area", "device_name", "final", "tipe", "urusan_count"])
            
            # Check ranking sorted by final desc
            ranking_sorted = True
            if len(data.get("ranking", [])) > 1:
                finals = [r["final"] for r in data["ranking"]]
                ranking_sorted = finals == sorted(finals, reverse=True)
            
            session.log("GET /stats/tipe-summary (penilai)", resp.status_code == 200 and has_counts and has_total and has_ranking,
                       f"Status: {resp.status_code}, Has all fields: {has_counts and has_total and has_ranking and has_pengali}")
            session.log("Stats tipe-summary sums match", sums_match,
                       f"sum(counts)={counts_sum}, total_devices={total_devices}, len(ranking)={ranking_len}")
            session.log("Stats tipe-summary ranking structure", ranking_valid)
            session.log("Stats tipe-summary ranking sorted by final desc", ranking_sorted)
        else:
            session.log("GET /stats/tipe-summary (penilai)", False, f"Status: {resp.status_code}")
    
    # Test with pengali=1.1
    if penilai_token:
        resp1 = session.get("/stats/tipe-summary", penilai_token, params={"pengali": 1})
        resp2 = session.get("/stats/tipe-summary", penilai_token, params={"pengali": 1.1})
        
        if resp1.status_code == 200 and resp2.status_code == 200:
            data1 = resp1.json()
            data2 = resp2.json()
            
            # Check that finals with pengali=1.1 are >= those with pengali=1
            if data1.get("ranking") and data2.get("ranking"):
                finals1 = [r["final"] for r in data1["ranking"]]
                finals2 = [r["final"] for r in data2["ranking"]]
                
                # Match by device_name
                map1 = {r["device_name"]: r["final"] for r in data1["ranking"]}
                map2 = {r["device_name"]: r["final"] for r in data2["ranking"]}
                
                all_greater = all(map2.get(name, 0) >= map1.get(name, 0) for name in map1.keys())
                session.log("Stats tipe-summary pengali=1.1 finals >= pengali=1", all_greater)
    
    # Test perangkat can access tipe-summary
    if perangkat_token:
        resp = session.get("/stats/tipe-summary", perangkat_token)
        session.log("GET /stats/tipe-summary (perangkat)", resp.status_code == 200,
                   f"Status: {resp.status_code}")
    
    # Test /stats/tipe-by-area (admin, penilai only)
    if penilai_token:
        resp = session.get("/stats/tipe-by-area", penilai_token)
        if resp.status_code == 200:
            data = resp.json()
            is_array = isinstance(data, list)
            has_structure = True
            if is_array and data:
                first = data[0]
                has_structure = all(k in first for k in ["area", "A", "B", "C", "Lainnya", "total"])
            
            session.log("GET /stats/tipe-by-area (penilai)", resp.status_code == 200 and is_array and has_structure,
                       f"Status: {resp.status_code}, Array: {is_array}, Count: {len(data) if is_array else 0}")
        else:
            session.log("GET /stats/tipe-by-area (penilai)", False, f"Status: {resp.status_code}")
    
    if admin_token:
        resp = session.get("/stats/tipe-by-area", admin_token)
        session.log("GET /stats/tipe-by-area (admin)", resp.status_code == 200,
                   f"Status: {resp.status_code}")
    
    # Test perangkat should get 403
    if perangkat_token:
        resp = session.get("/stats/tipe-by-area", perangkat_token)
        session.log("GET /stats/tipe-by-area (perangkat) returns 403", resp.status_code == 403,
                   f"Status: {resp.status_code}")
    
    # Test /stats/rekap-penilaian (admin, penilai only)
    if penilai_token:
        resp = session.get("/stats/rekap-penilaian", penilai_token)
        if resp.status_code == 200:
            data = resp.json()
            is_array = isinstance(data, list)
            has_15_areas = len(data) == 15 if is_array else False
            
            has_structure = True
            if is_array and data:
                first = data[0]
                required_fields = ["area", "level", "selesai", "menunggu_penilaian", "devices", "progress", "status", "counts"]
                has_structure = all(k in first for k in required_fields)
                
                # Check status values
                valid_statuses = all(d["status"] in ["selesai", "berjalan", "belum_ada"] for d in data)
                has_structure = has_structure and valid_statuses
            
            session.log("GET /stats/rekap-penilaian (penilai)", resp.status_code == 200 and is_array and has_structure,
                       f"Status: {resp.status_code}, Array: {is_array}, Count: {len(data) if is_array else 0}")
            session.log("Stats rekap-penilaian has 15 areas", has_15_areas,
                       f"Count: {len(data) if is_array else 0}")
        else:
            session.log("GET /stats/rekap-penilaian (penilai)", False, f"Status: {resp.status_code}")
    
    # Test verifikator should get 403
    if verifikator_token:
        resp = session.get("/stats/rekap-penilaian", verifikator_token)
        session.log("GET /stats/rekap-penilaian (verifikator) returns 403", resp.status_code == 403,
                   f"Status: {resp.status_code}")

def test_file_download(session: TestSession):
    """Test file download and meta endpoints"""
    print("\n=== FILE DOWNLOAD TESTS ===")
    
    penilai_token = session.tokens.get("penilai")
    
    if not penilai_token:
        session.log("File download tests", False, "No penilai token")
        return
    
    # Get a submission with uploads
    resp = session.get("/submissions", penilai_token)
    if resp.status_code != 200:
        session.log("Get submissions", False, f"Status {resp.status_code}")
        return
    
    submissions = resp.json()
    file_id = None
    
    for sub in submissions:
        uploads = sub.get("uploads", {})
        if uploads:
            for indicator_id, upload_data in uploads.items():
                if upload_data and "file_id" in upload_data:
                    file_id = upload_data["file_id"]
                    break
        if file_id:
            break
    
    if not file_id:
        session.log("File download tests", False, "No uploaded files found")
        return
    
    session.log("Found uploaded file", True, f"ID: {file_id[:8]}...")
    
    # Test download without auth should return 401
    resp = requests.get(f"{API_URL}/files/{file_id}/download", timeout=30)
    session.log("GET /files/{id}/download without auth returns 401", resp.status_code == 401,
               f"Status: {resp.status_code}")
    
    # Test download with Bearer token
    resp = session.get(f"/files/{file_id}/download", penilai_token)
    has_disposition = "content-disposition" in resp.headers and "inline" in resp.headers.get("content-disposition", "").lower()
    session.log("GET /files/{id}/download with Bearer", resp.status_code == 200 and has_disposition,
               f"Status: {resp.status_code}, Content-Disposition: {has_disposition}")
    
    # Test /files/{id}/meta
    resp = session.get(f"/files/{file_id}/meta", penilai_token)
    if resp.status_code == 200:
        data = resp.json()
        has_fields = all(k in data for k in ["id", "original_filename", "content_type", "url"])
        session.log("GET /files/{id}/meta", has_fields,
                   f"Status: {resp.status_code}, Has all fields: {has_fields}")
        
        # Test download via url with token
        if "url" in data:
            url = data["url"]
            # URL should contain ?t=token
            has_token_param = "?t=" in url
            session.log("File meta URL contains token param", has_token_param,
                       f"URL: {url[:80]}...")
            
            # Test download via URL without any auth header
            resp = requests.get(url, timeout=30)
            session.log("GET file URL without auth header", resp.status_code == 200,
                       f"Status: {resp.status_code}")
            
            # Test tampered token should return 401
            tampered_url = url.rsplit("=", 1)[0] + "=abc"
            resp = requests.get(tampered_url, timeout=30)
            session.log("GET file URL with tampered token returns 401", resp.status_code == 401,
                       f"Status: {resp.status_code}")
    else:
        session.log("GET /files/{id}/meta", False, f"Status: {resp.status_code}")

def main():
    print("=" * 60)
    print("BALANGA BACKEND API TESTS")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"API URL: {API_URL}")
    print()
    
    session = TestSession()
    
    # Run all tests
    test_regression(session)
    test_notifications(session)
    test_notification_flow(session)
    test_berita_acara(session)
    test_reports_rekap(session)
    test_stats_endpoints(session)
    test_file_download(session)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in session.results if r["passed"])
    failed = sum(1 for r in session.results if not r["passed"])
    total = len(session.results)
    
    print(f"Total: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if failed > 0:
        print("\nFailed Tests:")
        for r in session.results:
            if not r["passed"]:
                print(f"  ❌ {r['test']}")
                if r["message"]:
                    print(f"     {r['message']}")
    
    print("\n" + "=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
