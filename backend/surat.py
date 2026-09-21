import io
import re
from datetime import datetime
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph, Frame, Spacer
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def fmt_tanggal(iso: str) -> str:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


def fmt_waktu(iso: str) -> str:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return f"{d.strftime('%H:%M')} WIB, {fmt_tanggal(iso)}"


def tempat_surat(area: str) -> str:
    if area.lower().startswith("provinsi"):
        return "Palangka Raya"
    return re.sub(r"^(Kota|Kabupaten)\s+", "", area).strip()


def qr_payload(s: dict) -> str:
    v = s.get("verification") or {}
    urusan = s["urusan"] + (f" — {s['sub_urusan']}" if s.get("sub_urusan") else "")
    return (
        "SURAT KETERANGAN VERIFIKASI - Si-Scoring Kalteng\n"
        f"Verifikator : {v.get('verifikator_name', '-')}\n"
        f"Waktu Verifikasi : {fmt_waktu(v['verified_at']) if v.get('verified_at') else '-'}\n"
        f"Perangkat Daerah : {s['device_name']}\n"
        f"Area : {s['area']}\n"
        f"Urusan : {urusan}\n"
        f"ID Pengajuan : {s['id']}"
    )


def build_surat_pdf(s: dict) -> bytes:
    v = s.get("verification") or {}
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    margin = 2.5 * cm

    body = ParagraphStyle("body", fontName="Times-Roman", fontSize=12, leading=18, alignment=TA_JUSTIFY)
    center = ParagraphStyle("center", fontName="Times-Roman", fontSize=12, leading=18, alignment=TA_CENTER)
    title = ParagraphStyle("title", fontName="Times-Bold", fontSize=15, leading=20, alignment=TA_CENTER)
    sub = ParagraphStyle("sub", fontName="Times-Bold", fontSize=12, leading=16, alignment=TA_CENTER)
    status_style = ParagraphStyle("status", fontName="Times-Bold", fontSize=16, leading=22, alignment=TA_CENTER, textColor=colors.HexColor("#065f46"))

    c.setFont("Times-Bold", 12)
    c.drawCentredString(W / 2, H - margin + 0.6 * cm, "PEMERINTAH PROVINSI KALIMANTAN TENGAH")
    c.setStrokeColor(colors.black); c.setLineWidth(1.5)
    c.line(margin, H - margin - 0.1 * cm, W - margin, H - margin - 0.1 * cm)

    urusan = s["urusan"] + (f" — {s['sub_urusan']}" if s.get("sub_urusan") else "")
    story = [
        Spacer(1, 0.8 * cm),
        Paragraph("SURAT KETERANGAN VERIFIKASI", title),
        Paragraph("INSPEKTORAT", sub),
        Spacer(1, 1.2 * cm),
        Paragraph(
            f"Melalui surat ini, kami menyatakan bahwa seluruh dokumen dan berkas dari <b>{s['device_name']}</b> "
            f"<b>{s['area']}</b> perihal Urusan <b>{urusan}</b> telah melalui tahapan pemeriksaan dan peninjauan "
            "secara seksama. Berdasarkan hasil peninjauan tersebut, dengan ini dinyatakan bahwa berkas telah ditetapkan pada status:",
            body),
        Spacer(1, 0.8 * cm),
        Paragraph("\"TELAH DIVERIFIKASI\"", status_style),
        Spacer(1, 0.8 * cm),
        Paragraph("Demikian keterangan ini dibuat dengan sebenar-benarnya agar dapat dipergunakan sebagaimana mestinya.", body),
    ]
    frame = Frame(margin, H - margin - 11.5 * cm, W - 2 * margin, 11 * cm, showBoundary=0)
    frame.addFromList(story, c)

    tgl = fmt_tanggal(v["verified_at"]) if v.get("verified_at") else "-"
    sig_x = W - margin - 7.5 * cm
    sig_top = H - margin - 11.5 * cm
    sig_h = 6.5 * cm
    Frame(sig_x, sig_top - sig_h, 7.5 * cm, sig_h, showBoundary=0).addFromList([
        Paragraph(f"{tempat_surat(s['area'])}, {tgl}", center),
        Paragraph("Mengetahui,", center),
        Paragraph("Tim Verifikasi Inspektorat", center),
        Spacer(1, 2.2 * cm),
        Paragraph(f"( {v.get('verifikator_name', '-')} )", center),
    ], c)

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=1)
    qr.add_data(qr_payload(s)); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    box = 3 * cm
    qx, qy = margin, sig_top - sig_h + 0.9 * cm
    c.setLineWidth(1); c.rect(qx, qy, box, box)
    c.drawImage(ImageReader(img), qx + 0.1 * cm, qy + 0.1 * cm, box - 0.2 * cm, box - 0.2 * cm)
    c.setFont("Times-Italic", 8)
    c.drawString(qx, qy - 0.4 * cm, "Pindai QR untuk memeriksa keaslian verifikasi")

    c.setFont("Times-Italic", 8); c.setFillColor(colors.grey)
    c.drawString(margin, 1.5 * cm, f"Dokumen ini diterbitkan secara elektronik oleh Si-Scoring Kalteng · ID {s['id']}")
    c.showPage(); c.save()
    return buf.getvalue()
