import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, formatApiErrorDetail, openFile, downloadSurat } from "../lib/api";
import { Navbar } from "../components/Navbar";
import { StatusPill } from "../components/StatusPill";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Checkbox } from "../components/ui/checkbox";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle2, XCircle, FileText, ExternalLink, FileBadge, ShieldCheck, Layers } from "lucide-react";

const ACK_TEXT = "Saya mengakui telah membaca dan memeriksa secara menyeluruh semua berkas yang diajukan";

export default function VerifikatorReviewPage() {
  const { sid } = useParams();
  const navigate = useNavigate();
  const [s, setS] = useState(null);
  const [period, setPeriod] = useState(null);
  const [inds, setInds] = useState({ umum: [], teknis: [] });
  const [ack, setAck] = useState(false);
  const [rejectMode, setRejectMode] = useState(false);
  const [rejectNote, setRejectNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const [sub, p] = await Promise.all([api.get(`/submissions/${sid}`), api.get("/periods/active")]);
      setS(sub.data); setPeriod(p.data && p.data.id ? p.data : null);
      const { data } = await api.get("/indicators/for-submission", { params: { level: sub.data.level, urusan: sub.data.urusan, sub_urusan: sub.data.sub_urusan || undefined } });
      setInds(data);
    } catch (e) { setError(formatApiErrorDetail(e.response?.data?.detail)); }
  }, [sid]);
  useEffect(() => { load(); }, [load]);

  const act = async (action) => {
    if (action === "approve" && !ack) return toast.error("Centang pernyataan terlebih dahulu");
    if (action === "reject" && !rejectNote.trim()) return toast.error("Catatan perbaikan wajib diisi");
    setBusy(true);
    try {
      await api.post(`/submissions/${sid}/verify`, { action, notes: rejectNote, acknowledged: ack });
      toast.success(action === "approve" ? "Terverifikasi, diteruskan ke penilai" : "Dikembalikan ke perangkat");
      await load(); setRejectMode(false); setRejectNote("");
    } catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail)); }
    setBusy(false);
  };

  const all = [...inds.umum, ...inds.teknis];
  const uploaded = all.filter((i) => (s?.uploads || {})[i.id]).length;
  const verified = s && ["menunggu_penilaian", "selesai"].includes(s.status) && s.verification;
  const fmt = (d) => d ? new Date(d).toLocaleString("id-ID", { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "-";

  return (
    <div className="min-h-screen bg-background">
      <Navbar period={period} />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8" data-testid="verif-review-page">
        <button data-testid="back-to-verif-list" onClick={() => navigate("/")} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-slate-900 mb-4"><ArrowLeft className="w-4 h-4" /> Kembali ke daftar</button>
        {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" data-testid="verif-review-error">{error}</div>}
        {s && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-3 mb-6">
              <div>
                <h1 className="font-display text-2xl sm:text-3xl font-extrabold text-slate-900" data-testid="verif-review-title">{s.device_name}</h1>
                <div className="text-sm text-muted-foreground mt-1">{s.area} · {s.urusan}{s.sub_urusan ? ` — ${s.sub_urusan}` : ""} · Tahun {s.year}</div>
                <div className="text-xs text-muted-foreground mt-0.5">Pemohon: {s.perangkat_name}</div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <StatusPill status={s.status} />
                <span className="text-xs text-muted-foreground" data-testid="verif-file-count">{uploaded}/{all.length} berkas tersedia</span>
              </div>
            </div>

            {verified && (
              <div className="mb-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 flex flex-wrap items-center justify-between gap-4" data-testid="verif-done-banner">
                <div className="flex items-start gap-3">
                  <ShieldCheck className="w-6 h-6 text-emerald-700 mt-0.5" />
                  <div>
                    <div className="font-semibold text-emerald-900">Telah Diverifikasi</div>
                    <div className="text-sm text-emerald-800">oleh {s.verification.verifikator_name} · {fmt(s.verification.verified_at)}</div>
                    {s.verification.notes && <div className="text-xs text-emerald-700 mt-1 italic">"{s.verification.notes}"</div>}
                  </div>
                </div>
                <Button className="gap-2" data-testid="download-surat-btn" onClick={() => downloadSurat(s.id)}><FileBadge className="w-4 h-4" /> Unduh Surat Keterangan (PDF + QR)</Button>
              </div>
            )}

            <section className="space-y-6">
              <FileGroup title="Faktor Umum" icon={<Layers className="w-4 h-4 text-accent" />} list={inds.umum} s={s} />
              <FileGroup title={`Faktor Teknis — ${s.urusan}`} icon={<Layers className="w-4 h-4 text-primary" />} list={inds.teknis} s={s} />
            </section>

            {s.status === "menunggu_verifikasi" && (
              <div className="mt-8 rounded-2xl border border-border bg-white p-5 space-y-4" data-testid="verif-action-panel">
                <label className="flex items-start gap-3 cursor-pointer select-none">
                  <Checkbox checked={ack} onCheckedChange={(v) => setAck(!!v)} data-testid="verif-ack-checkbox" className="mt-0.5" />
                  <span className="text-sm text-slate-800 leading-relaxed">{ACK_TEXT}</span>
                </label>
                {rejectMode && <Textarea data-testid="reject-note-input" placeholder="Catatan perbaikan untuk perangkat daerah..." value={rejectNote} onChange={(e) => setRejectNote(e.target.value)} rows={3} />}
                <div className="flex flex-col sm:flex-row gap-3">
                  {!rejectMode ? (
                    <>
                      <Button className="flex-1 gap-2 h-11" data-testid="verify-approve-btn" disabled={!ack || busy} onClick={() => act("approve")}><CheckCircle2 className="w-4 h-4" /> Setujui & Teruskan ke Penilai</Button>
                      <Button variant="outline" className="flex-1 gap-2 h-11 text-red-600 border-red-300 hover:bg-red-50 hover:text-red-700" data-testid="verify-reject-mode-btn" onClick={() => setRejectMode(true)}><XCircle className="w-4 h-4" /> Kembalikan untuk Perbaikan</Button>
                    </>
                  ) : (
                    <>
                      <Button variant="destructive" className="flex-1 gap-2 h-11" data-testid="verify-reject-confirm-btn" disabled={busy} onClick={() => act("reject")}><XCircle className="w-4 h-4" /> Kirim Catatan Perbaikan</Button>
                      <Button variant="ghost" className="flex-1 h-11" data-testid="verify-reject-cancel-btn" onClick={() => setRejectMode(false)}>Batal</Button>
                    </>
                  )}
                </div>
                {!ack && <p className="text-xs text-muted-foreground">Tombol "Setujui" aktif setelah pernyataan dicentang.</p>}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function FileGroup({ title, icon, list, s }) {
  const fmt = (d) => d ? new Date(d).toLocaleString("id-ID", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "-";
  return (
    <div>
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">{icon} {title}</div>
      <div className="rounded-2xl border border-border bg-white divide-y divide-border">
        {list.length === 0 && <div className="px-4 py-6 text-sm text-muted-foreground text-center">Tidak ada indikator.</div>}
        {list.map((ind) => {
          const up = (s.uploads || {})[ind.id];
          return (
            <div key={ind.id} className="px-4 py-3 flex items-center justify-between gap-4" data-testid={`verif-file-row-${ind.id}`}>
              <div className="min-w-0">
                <div className="text-sm font-medium text-slate-800"><span className="text-muted-foreground mr-1">{ind.order}.</span>{ind.name}</div>
                {up ? <div className="text-xs text-muted-foreground mt-0.5 truncate">{up.original_filename} · diunggah {fmt(up.uploaded_at)}</div> : <div className="text-xs text-red-600 mt-0.5">Berkas tidak ada</div>}
              </div>
              {up && <Button variant="outline" size="sm" className="gap-1.5 shrink-0 text-emerald-700 border-emerald-300 hover:bg-emerald-50" data-testid={`view-file-${ind.id}`} onClick={() => openFile(up.file_id, up.original_filename)}><FileText className="w-4 h-4" /> Buka Berkas <ExternalLink className="w-3 h-3" /></Button>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
