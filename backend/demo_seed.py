import io
import random
import uuid
import logging
from datetime import datetime, timezone, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)
KELAS = ["a", "b", "c", "d", "e"]
TRANTIB = "Bidang Ketentraman dan Ketertiban Umum serta Perlindungan Masyarakat"

DEMO_USERS = [
    ("perangkat.kapuas@kalteng.go.id", "Kerja123!", "Dinas Kesehatan Kabupaten Kapuas", "perangkat", "Kabupaten Kapuas"),
    ("perangkat.kotim@kalteng.go.id", "Kerja123!", "Dinas PUPR Kabupaten Kotawaringin Timur", "perangkat", "Kabupaten Kotawaringin Timur"),
    ("perangkat.provinsi@kalteng.go.id", "Kerja123!", "Dinas Pendidikan Provinsi Kalimantan Tengah", "perangkat", "Provinsi Kalimantan Tengah"),
    ("verifikator.kapuas@kalteng.go.id", "Verif123!", "Verifikator Kapuas", "verifikator", "Kabupaten Kapuas"),
    ("verifikator.kotim@kalteng.go.id", "Verif123!", "Verifikator Kotawaringin Timur", "verifikator", "Kabupaten Kotawaringin Timur"),
    ("verifikator.provinsi@kalteng.go.id", "Verif123!", "Verifikator Provinsi", "verifikator", "Provinsi Kalimantan Tengah"),
]

# (perangkat_email, device_name, urusan, sub_urusan, status, year_offset, kelas_bias)
DEMO_SUBS = [
    ("perangkat@kalteng.go.id", "Dinas Pendidikan Kota Palangka Raya", "Bidang Pendidikan", None, "selesai", 0, 4),
    ("perangkat@kalteng.go.id", "Dinas Pendidikan Kota Palangka Raya", "Bidang Kebudayaan", None, "selesai", 0, 3),
    ("perangkat@kalteng.go.id", "Dinas Pendidikan Kota Palangka Raya", "Bidang Pendidikan", None, "selesai", -1, 3),
    ("perangkat@kalteng.go.id", "Satpol PP Kota Palangka Raya", TRANTIB, "Urusan Ketentraman dan Ketertiban Umum", "menunggu_verifikasi", 0, 3),
    ("perangkat@kalteng.go.id", "Dinas Sosial Kota Palangka Raya", "Bidang Sosial", None, "ditolak", 0, 2),
    ("perangkat@kalteng.go.id", "Dinas Perhubungan Kota Palangka Raya", "Bidang Perhubungan", None, "draft", 0, 2),
    ("perangkat.kapuas@kalteng.go.id", "Dinas Kesehatan Kabupaten Kapuas", "Bidang Kesehatan", None, "selesai", 0, 3),
    ("perangkat.kapuas@kalteng.go.id", "Dinas Kesehatan Kabupaten Kapuas", "Bidang Kesehatan", None, "selesai", -1, 2),
    ("perangkat.kapuas@kalteng.go.id", "Dinas Pertanian Kabupaten Kapuas", "Bidang Pertanian", None, "menunggu_penilaian", 0, 3),
    ("perangkat.kotim@kalteng.go.id", "Dinas PUPR Kabupaten Kotawaringin Timur", "Bidang Pekerjaan Umum dan Penataan Ruang", None, "selesai", 0, 4),
    ("perangkat.kotim@kalteng.go.id", "Dinas PUPR Kabupaten Kotawaringin Timur", "Bidang Perumahan dan Kawasan Permukiman", None, "menunggu_penilaian", 0, 3),
    ("perangkat.kotim@kalteng.go.id", "Kecamatan Baamang", "Kecamatan", None, "selesai", 0, 3),
    ("perangkat.provinsi@kalteng.go.id", "Dinas Pendidikan Provinsi Kalimantan Tengah", "Bidang Pendidikan", None, "selesai", 0, 4),
    ("perangkat.provinsi@kalteng.go.id", "Dinas Kehutanan Provinsi Kalimantan Tengah", "Bidang Kehutanan", None, "menunggu_verifikasi", 0, 3),
    ("perangkat.provinsi@kalteng.go.id", "Dinas Kehutanan Provinsi Kalimantan Tengah", "Bidang Kehutanan", None, "selesai", -1, 4),
]


def _demo_pdf() -> bytes:
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16); c.drawString(72, 770, "DOKUMEN BUKTI CONTOH (DEMO)")
    c.setFont("Helvetica", 11)
    for i, line in enumerate([
        "Dokumen ini dibuat otomatis sebagai data contoh Si-Scoring Kalteng.",
        "Data indikator (contoh): Jumlah penduduk 305.000 jiwa; Luas wilayah 2.678 km2;",
        "Jumlah APBD Rp 1,45 triliun; Jumlah satuan pendidikan dasar 312 unit;",
        "Jumlah anak usia pendidikan dasar 58.400 jiwa; Kurikulum muatan lokal 4 dokumen.",
        "Sumber: BPS Kalimantan Tengah & Perda APBD (ilustrasi).",
    ]):
        c.drawString(72, 740 - i * 18, line)
    c.showPage(); c.save()
    return buf.getvalue()


def _iso(days_ago: int, hour: int = 9) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).replace(hour=hour, minute=random.randint(0, 59), second=0, microsecond=0).isoformat()


def _pick_kelas(bias: int, rng: random.Random) -> int:
    return max(0, min(4, int(rng.gauss(bias, 0.9))))


async def seed_demo(db, hash_password, put_object, area_level: dict, app_name: str):
    if await db.submissions.count_documents({}) > 0:
        return
    rng = random.Random(18)
    for email, pw, name, role, area in DEMO_USERS:
        if not await db.users.find_one({"email": email}):
            await db.users.insert_one({"id": str(uuid.uuid4()), "email": email, "name": name, "role": role, "area": area,
                                       "active": True, "password_hash": hash_password(pw), "created_at": _iso(120)})
    users = {u["email"]: u for u in await db.users.find({}).to_list(500)}
    verifs = {u["area"]: u for u in users.values() if u["role"] == "verifikator"}
    penilai = next((u for u in users.values() if u["role"] == "penilai"), None)

    year = datetime.now(timezone.utc).year
    periods = {p["year"]: p for p in await db.periods.find({}).to_list(50)}
    if year - 1 not in periods:
        p = {"id": str(uuid.uuid4()), "year": year - 1, "name": f"Evaluasi Perangkat Daerah {year - 1}", "start_date": f"{year - 1}-01-01",
             "end_date": f"{year - 1}-12-31", "upload_locked": True, "active": False, "created_at": _iso(400)}
        await db.periods.insert_one(p); periods[year - 1] = p

    file_meta = None
    try:
        fid = str(uuid.uuid4()); path = f"{app_name}/demo/{fid}.pdf"
        res = put_object(path, _demo_pdf(), "application/pdf")
        await db.files.insert_one({"id": fid, "storage_path": res["path"], "original_filename": "bukti_dukung_contoh.pdf", "content_type": "application/pdf",
                                   "submission_id": None, "is_deleted": False, "created_at": _iso(60)})
        file_meta = {"file_id": fid, "original_filename": "bukti_dukung_contoh.pdf", "uploaded_at": _iso(60)}
    except Exception as e:
        logger.warning(f"Demo file upload skipped: {e}")

    umum = await db.indicators.find({"type": "umum"}).sort("order", 1).to_list(20)
    for email, device, urusan, sub, status, yoff, bias in DEMO_SUBS:
        u = users.get(email)
        if not u: continue
        area = u["area"]; level = area_level.get(area)
        teknis = await db.indicators.find({"type": "teknis", "level": level, "urusan": urusan, "sub_urusan": sub}).sort("order", 1).to_list(100)
        inds = umum + teknis
        period = periods.get(year + yoff)
        base_days = 300 if yoff < 0 else rng.randint(8, 40)
        created = _iso(base_days)
        uploads = {i["id"]: file_meta for i in inds} if (file_meta and status != "draft") else {}
        if status == "draft" and file_meta:
            uploads = {i["id"]: file_meta for i in inds[: max(1, len(inds) // 2)]}
        hist = [{"status": "draft", "at": created, "by": u["name"]}]
        audit = [{"action": "Membuat pengajuan", "by": u["name"], "by_role": "perangkat", "at": created, "detail": urusan}]
        verification = None; scoring = None; rejection = None
        if status != "draft":
            t = _iso(base_days - 2)
            hist.append({"status": "menunggu_verifikasi", "at": t, "by": u["name"]})
            audit.append({"action": "Mengirim untuk verifikasi", "by": u["name"], "by_role": "perangkat", "at": t, "detail": ""})
        v = verifs.get(area)
        if status == "ditolak" and v:
            t = _iso(base_days - 3); rejection = "Berkas indikator Jumlah PMKS belum mencantumkan sumber data resmi. Mohon lengkapi."
            hist.append({"status": "ditolak", "at": t, "by": v["name"], "note": rejection})
            verification = {"verifikator_id": v["id"], "verifikator_name": v["name"], "notes": rejection, "verified_at": t, "acknowledged": True}
            audit.append({"action": "Dikembalikan untuk perbaikan", "by": v["name"], "by_role": "verifikator", "at": t, "detail": rejection})
        if status in ("menunggu_penilaian", "selesai") and v:
            t = _iso(base_days - 4)
            hist.append({"status": "menunggu_penilaian", "at": t, "by": v["name"]})
            verification = {"verifikator_id": v["id"], "verifikator_name": v["name"], "notes": "Berkas lengkap dan sesuai.", "verified_at": t, "acknowledged": True}
            audit.append({"action": "Verifikasi disetujui", "by": v["name"], "by_role": "verifikator", "at": t, "detail": "Berkas lengkap dan sesuai."})
        if status == "selesai" and penilai:
            t = _iso(base_days - 6)
            vals = {}; umum_total = 0; teknis_total = 0
            for i in inds:
                scores = i.get("scores") or [200, 400, 600, 800, 1000]
                k = _pick_kelas(bias, rng); sc = scores[k]
                vals[i["id"]] = {"indicator_name": i["name"], "ok": True, "note": "", "data_validasi": str(rng.randint(10, 9000)), "kelas": KELAS[k], "score": sc}
                if i["type"] == "umum": umum_total += sc
                else: teknis_total += sc
            scoring = {"penilai_id": penilai["id"], "penilai_name": penilai["name"], "validations": vals, "umum_total": umum_total,
                       "teknis_total": teknis_total, "total": umum_total + teknis_total, "overall_note": "Data contoh (demo).", "scored_at": t}
            hist.append({"status": "selesai", "at": t, "by": penilai["name"]})
            audit.append({"action": "Penilaian selesai", "by": penilai["name"], "by_role": "penilai", "at": t, "detail": f"Umum {umum_total} / Teknis {teknis_total}"})
        await db.submissions.insert_one({
            "id": str(uuid.uuid4()), "period_id": period["id"], "year": period["year"], "area": area, "level": level,
            "device_name": device, "urusan": urusan, "sub_urusan": sub, "perangkat_user_id": u["id"], "perangkat_name": u["name"],
            "status": status, "uploads": uploads, "verification": verification, "scoring": scoring, "rejection_note": rejection,
            "history": hist, "audit": audit, "created_at": created, "updated_at": hist[-1]["at"]})
    logger.info("Demo submissions seeded")
