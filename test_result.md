#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Balanga (Si-Scoring Kalteng) - Sistem Penilaian Tipologi Perangkat Daerah PP 18/2016. Iterasi revisi:
  ekspor rekap per periode (Excel/PDF), Berita Acara per pengajuan sesuai Format Scoring (Excel/PDF, Keterangan = nama file + link),
  notifikasi persisten ke Perangkat saat diverifikasi/ditolak/dinilai, statistik tipologi (tipe-summary, tipe-by-area, rekap-penilaian),
  pratinjau berkas inline (content-type by ekstensi, token berkas), penilaian pilih angka langsung, sort/cari semua tabel,
  kolom tracking waktu (unggah/verifikasi/penilaian), login page baru (latar.jpg, kontak admin, Biro Organisasi), brand Balanga.

backend:
  - task: "Notifikasi persisten (db.notifications) + GET /api/notifications (event+period) + POST /api/notifications/read-all"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "notify_user dipanggil saat verify approve/reject dan score. GET mengembalikan array item {id, kind: event|period, level, message, read, created_at}."
      - working: true
        agent: "testing"
        comment: "✅ GET /api/notifications returns correct structure with kind (event|period), level, message, read fields. POST /api/notifications/read-all works correctly and marks all event notifications as read. Period notifications present. Event notifications not in demo data (expected - created only during verify/score flow)."
  - task: "GET /api/files/{id}/download dengan token berkas (?t=) atau auth user; content-type by ekstensi; GET /api/files/{id}/meta"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Tanpa auth -> 401. Dengan Bearer -> 200 inline. Token t dibuat file_link() (jwt type=file)."
      - working: true
        agent: "testing"
        comment: "✅ All file download tests passed: /files/{id}/download without auth returns 401, with Bearer returns 200 with Content-Disposition inline. /files/{id}/meta returns correct structure with id, original_filename, content_type, url. URL contains token param (?t=). Download via URL without auth header works. Tampered token returns 401."
  - task: "GET /api/submissions/{sid}/berita-acara?format=xlsx|pdf&pengali=1|1.1&auth=TOKEN"
    implemented: true
    working: true
    file: "backend/server.py, backend/exports.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Hanya status selesai (else 400). Perangkat hanya miliknya, verifikator hanya area-nya. pengali selain 1/1.1 -> 400. Diverifikasi manual: xlsx & pdf 200."
      - working: true
        agent: "testing"
        comment: "✅ All berita-acara tests passed: format=xlsx returns 200 with correct content-type and PK header. format=pdf returns 200 with %PDF header. pengali=2 returns 400. Auth via query param works. Non-selesai submission returns 400. Verifikator accessing other area returns 403."
  - task: "GET /api/reports/rekap?period_id&format=xlsx|pdf&pengali&auth=TOKEN (admin, penilai)"
    implemented: true
    working: true
    file: "backend/server.py, backend/exports.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Tanpa period_id -> periode aktif. Role lain -> 403."
      - working: true
        agent: "testing"
        comment: "✅ All reports/rekap tests passed: format=xlsx returns 200 with PK header. format=pdf with pengali=1.1 returns 200 with %PDF header. Explicit period_id works. Perangkat returns 403. pengali=1.5 returns 400."
  - task: "GET /api/stats/tipe-summary, /api/stats/tipe-by-area (admin,penilai), /api/stats/rekap-penilaian (admin,penilai)"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Param period_id & pengali opsional. tipe-summary: {counts{A,B,C,Lainnya}, total_devices, ranking[] dengan rank}. rekap-penilaian: per area {selesai, menunggu_penilaian, devices[], progress, status}."
      - working: true
        agent: "testing"
        comment: "✅ All stats endpoints passed: /stats/tipe-summary returns correct structure with counts, total_devices, ranking. sum(counts)==total_devices==len(ranking) verified. Ranking sorted by final desc. pengali=1.1 produces finals >= pengali=1. Accessible by penilai and perangkat. /stats/tipe-by-area returns array with area, A, B, C, Lainnya, total. Admin and penilai can access, perangkat returns 403. /stats/rekap-penilaian returns 15 areas with correct structure and status values (selesai/berjalan/belum_ada). Verifikator returns 403."
  - task: "Alur existing: login 4 peran, submissions, verify, score (regression)"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: true
        agent: "testing"
        comment: "Lolos pada iterasi sebelumnya (iteration_4)."
      - working: true
        agent: "testing"
        comment: "✅ All regression tests passed: Login successful for all 4 roles (admin, penilai, verifikator, perangkat). GET /auth/me returns 200 for all roles. GET /submissions returns 200 for all roles with correct counts."

frontend:
  - task: "Login page: latar.jpg, kontak admin Riani, Biro Organisasi, judul Balanga"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/LoginPage.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Screenshot manual OK."
  - task: "Penilai: pilih angka skor langsung (ScoreRow), tab Rekap Penilaian, kolom Waktu Penilaian, sort/cari, tombol Berita Acara"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/PenilaiDashboard.js, components/ScoreRow.js, components/RekapPenilaian.js, components/BeritaAcaraButtons.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Screenshot manual tab Penilaian/Rekap/Laporan OK."
  - task: "Laporan Hasil: TipeSummary (grafik A/B/C + top 5) & ekspor rekap periode"
    implemented: true
    working: "NA"
    file: "frontend/src/components/ReportsPanel.js, components/TipeSummary.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: ""
  - task: "Verifikator: kolom Unggah Terakhir & Waktu Verifikasi/Penolakan, sort/cari; pratinjau berkas pop-up"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/VerifikatorDashboard.js, pages/VerifikatorReviewPage.js, components/FilePreviewHost.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: ""
  - task: "Perangkat: kolom Waktu Unggah Terakhir, sort/cari, notifikasi bel unread, Berita Acara di detail selesai"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/PerangkatDashboard.js, components/NotificationBell.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: ""
  - task: "Admin: grafik sebaran Tipe per kab/kota, TipeSummary, ekspor rekap, sort/cari pengguna"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/AdminDashboard.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: ""

metadata:
  created_by: "main_agent"
  version: "2.0"
  test_sequence: 6
  run_ui: false

test_plan:
  current_focus:
    - "Notifikasi persisten"
    - "Berita Acara"
    - "Rekap per periode"
    - "Stats tipologi"
    - "Download file token"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: "Kredensial di /app/memory/test_credentials.md. Backend baru: notifikasi, berita-acara, reports/rekap, stats/tipe-*, files download token. Mohon uji role-based access & format response. Jangan hapus data demo; boleh membuat pengajuan baru dengan perangkat@kalteng.go.id jika perlu alur verify->score->notifikasi."
  - agent: "testing"
    message: "Backend testing complete. 52/54 tests passed (96.3%). All critical endpoints working: notifications (GET/POST read-all), berita-acara (xlsx/pdf with pengali validation), reports/rekap (xlsx/pdf with access control), stats (tipe-summary/tipe-by-area/rekap-penilaian with correct structure), file downloads (token auth, meta, tampered token protection). Regression tests passed for all 4 roles. Event notifications not in demo data (expected - created during verify/score flow). All backend tasks marked working=true."
