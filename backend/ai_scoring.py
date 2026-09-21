import asyncio
import json
import os
import re
import tempfile
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

logger = logging.getLogger(__name__)
KELAS = ["a", "b", "c", "d", "e"]
MODEL = ("gemini", "gemini-3.1-pro-preview")
SUPPORTED = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}

SYSTEM = (
    "Anda adalah asisten Tim Penilai Tipologi Perangkat Daerah berdasarkan PP 18/2016 (Kalimantan Tengah). "
    "Tugas Anda: membaca berkas bukti yang diunggah perangkat daerah, mengekstrak nilai data untuk setiap indikator yang diminta, "
    "lalu merekomendasikan kelas interval (a=terendah ... e=tertinggi) sesuai lampiran PP 18/2016 untuk tingkat pemerintahan terkait. "
    "Jawab HANYA dengan JSON valid tanpa teks lain."
)


def _prompt(s: dict, inds: list) -> str:
    lines = []
    for ind in inds:
        scores = ind.get("scores") or []
        deret = ", ".join(f"{k}={v}" for k, v in zip(KELAS, scores)) if scores else "tidak tersedia"
        lines.append(f'- id="{ind["id"]}" | indikator ({ind.get("type")}): "{ind.get("name")}" | deretan skor a-e: {deret}')
    return (
        f"Konteks: Tingkat pemerintahan = {s.get('level')}, Area = {s.get('area')}, Perangkat Daerah = {s.get('device_name')}, "
        f"Urusan = {s.get('urusan')}{' — ' + s['sub_urusan'] if s.get('sub_urusan') else ''}.\n"
        "Berkas bukti terlampir. Untuk SETIAP indikator berikut, ekstrak nilai data dari berkas (angka beserta satuan), "
        "tentukan kelas interval a-e yang paling sesuai menurut skala interval PP 18/2016 untuk tingkat pemerintahan ini, "
        "dan beri alasan singkat (maks 2 kalimat, Bahasa Indonesia). Jika berkas tidak memuat data relevan untuk suatu indikator, isi kelas null.\n"
        + "\n".join(lines)
        + '\nFormat jawaban: {"items": [{"id": "...", "kelas": "a"|"b"|"c"|"d"|"e"|null, "data_value": "string", "reason": "string", "confidence": 0.0-1.0}]}'
    )


def _parse(text: str) -> list:
    m = re.search(r"\{.*\}", text, re.S)
    try:
        data = json.loads(m.group(0) if m else text)
        return data.get("items", []) if isinstance(data, dict) else data
    except Exception:
        return []


async def _ask(prompt: str, tmp: str, mime: str, session: str) -> str:
    delays = [0, 3, 8, 15]
    last = None
    for d in delays:
        if d: await asyncio.sleep(d)
        try:
            chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=session, system_message=SYSTEM).with_model(*MODEL)
            return await chat.send_message(UserMessage(text=prompt, file_contents=[FileContentWithMimeType(mime_type=mime, file_path=tmp)]))
        except Exception as e:
            last = e
            if "429" not in str(e) and "RateLimit" not in str(e):
                raise
    raise last


def _base(ind: dict) -> dict:
    return {"indicator_id": ind["id"], "indicator_name": ind["name"], "kelas": None, "score": None, "data_value": "", "reason": "", "confidence": 0}


async def recommend_scores(s: dict, indicators: list, fetch_bytes) -> list:
    uploads = s.get("uploads") or {}
    results = {}
    groups = {}
    for ind in indicators:
        meta = uploads.get(ind["id"])
        if not meta:
            results[ind["id"]] = {**_base(ind), "reason": "Tidak ada berkas bukti untuk indikator ini."}
            continue
        ext = (meta.get("original_filename") or "").rsplit(".", 1)[-1].lower()
        if ext not in SUPPORTED:
            results[ind["id"]] = {**_base(ind), "reason": f"Format .{ext} belum dapat dianalisis AI (dukungan: PDF, PNG, JPG, WEBP)."}
            continue
        groups.setdefault(meta["file_id"], (ext, []))[1].append(ind)

    for file_id, (ext, inds) in groups.items():
        tmp = None
        try:
            data = await asyncio.to_thread(fetch_bytes, file_id)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as f:
                f.write(data); tmp = f.name
            raw = await _ask(_prompt(s, inds), tmp, SUPPORTED[ext], f"ai-{s['id']}-{file_id}")
            by_id = {str(it.get("id")): it for it in _parse(raw) if isinstance(it, dict)}
            for ind in inds:
                out = by_id.get(ind["id"], {})
                kelas = str(out.get("kelas") or "").lower() or None
                if kelas not in KELAS:
                    kelas = None
                scores = ind.get("scores") or []
                results[ind["id"]] = {**_base(ind), "kelas": kelas, "score": scores[KELAS.index(kelas)] if (kelas and scores) else None,
                                      "data_value": str(out.get("data_value") or ""), "reason": str(out.get("reason") or ("Tidak ada jawaban AI untuk indikator ini." if not out else "")),
                                      "confidence": out.get("confidence") or 0}
        except Exception as e:
            logger.error(f"AI recommend failed for file {file_id}: {e}")
            for ind in inds:
                results[ind["id"]] = {**_base(ind), "reason": f"Analisis AI gagal: {str(e)[:150]}"}
        finally:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)
    return [results[ind["id"]] for ind in indicators]
