import React, { useEffect, useState, useCallback, useMemo } from "react";
import { api, formatApiErrorDetail, openFile } from "../lib/api";
import { Navbar } from "../components/Navbar";
import { StatusPill } from "../components/StatusPill";
import { SubmissionScoreView } from "../components/SubmissionScoreView";
import { ReportsPanel } from "../components/ReportsPanel";
import { RekapPenilaian } from "../components/RekapPenilaian";
import { BeritaAcaraButtons } from "../components/BeritaAcaraButtons";
import { ScoreRow } from "../components/ScoreRow";
import { useTableTools, SearchBox, SortTh, fmtDateTime } from "../components/TableTools";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../components/ui/select";
import { toast } from "sonner";
import { ClipboardCheck, Eye, ArrowLeft, Sparkles, Loader2, Wand2, BarChart3 } from "lucide-react";

const KEYS = {
  device_name: "device_name", area: "area", urusan: (s) => `${s.urusan} ${s.sub_urusan || ""}`, year: "year",
  total: (s) => s.scoring?.total, verified_at: (s) => s.verification?.verified_at, scored_at: (s) => s.scoring?.scored_at,
};

function SubmissionTable({ list, action, onOpen, mode }) {
  const { query, setQuery, sort, toggleSort, rows } = useTableTools(list, KEYS, { key: mode === "done" ? "scored_at" : "verified_at", dir: "desc" });
  const timeKey = mode === "done" ? "scored_at" : "verified_at";
  const timeLabel = mode === "done" ? "Waktu Penilaian" : "Waktu Diverifikasi";
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SearchBox value={query} onChange={setQuery} placeholder="Cari perangkat daerah, area, urusan..." className="w-full sm:w-80" testId={`search-${mode}`} />
        <div className="text-xs text-muted-foreground">{rows.length} dari {list.length} pengajuan</div>
      </div>
      <div className="rounded-2xl border border-border bg-white overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left text-xs text-muted-foreground"><tr>
            <SortTh label="Perangkat Daerah" sortKey="device_name" sort={sort} onSort={toggleSort} />
            <SortTh label="Area" sortKey="area" sort={sort} onSort={toggleSort} />
            <SortTh label="Urusan" sortKey="urusan" sort={sort} onSort={toggleSort} />
            <SortTh label="Tahun" sortKey="year" sort={sort} onSort={toggleSort} />
            <SortTh label={timeLabel} sortKey={timeKey} sort={sort} onSort={toggleSort} />
            <SortTh label="Hasil" sortKey="total" sort={sort} onSort={toggleSort} />
            <th className="px-4 py-3 text-right">Aksi</th></tr></thead>
          <tbody>
            {rows.length === 0 && <tr><td colSpan={7} className="text-center py-12 text-muted-foreground">Tidak ada data.</td></tr>}
            {rows.map((s) => {
              const sc = s.scoring;
              return (
                <tr key={s.id} data-testid={`score-row-${s.id}`} className="border-t border-border">
                  <td className="px-4 py-3 font-medium text-slate-800">{s.device_name}</td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">{s.area}</td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">{s.urusan}{s.sub_urusan ? ` — ${s.sub_urusan}` : ""}</td>
                  <td className="px-4 py-3">{s.year}</td>
                  <td className="px-4 py-3 text-xs text-slate-600 whitespace-nowrap" data-testid={`time-${s.id}`}>{fmtDateTime(mode === "done" ? sc?.scored_at : s.verification?.verified_at)}</td>
                  <td className="px-4 py-3 font-mono text-xs">{sc ? `${sc.total} (U${sc.umum_total}/T${sc.teknis_total})` : "-"}</td>
                  <td className="px-4 py-3 text-right"><Button variant="outline" size="sm" className="gap-1.5" data-testid={`assess-btn-${s.id}`} onClick={() => onOpen(s)}><Eye className="w-4 h-4" /> {action}</Button></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function PenilaiDashboard() {
  const [subs, setSubs] = useState([]);
  const [period, setPeriod] = useState(null);
  const [activeId, setActiveId] = useState(null);
  const [inds, setInds] = useState({ umum: [], teknis: [] });
  const [rows, setRows] = useState({});
  const [overallNote, setOverallNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [ai, setAi] = useState(null);
  const [yearFilter, setYearFilter] = useState("all");

  const active = subs.find((s) => s.id === activeId) || null;

  const load = useCallback(async () => {
    const [s, p] = await Promise.all([api.get("/submissions"), api.get("/periods/active")]);
    setSubs(s.data); setPeriod(p.data && p.data.id ? p.data : null);
    return s.data;
  }, []);
  useEffect(() => { load(); }, [load]);

  const openScore = async (s) => {
    setActiveId(s.id); setOverallNote(""); setAi(s.ai_recommendation || null);
    const { data } = await api.get("/indicators/for-submission", { params: { level: s.level, urusan: s.urusan, sub_urusan: s.sub_urusan || undefined } });
    setInds(data);
    const init = {};
    [...data.umum, ...data.teknis].forEach((i) => { init[i.id] = { ok: true, note: "", data_validasi: "", kelas: "", score: "" }; });
    setRows(init);
  };

  const allInds = [...inds.umum, ...inds.teknis];
  const allScored = allInds.length > 0 && allInds.every((i) => rows[i.id]?.score !== "" && rows[i.id]?.score != null);
  const setRow = (id, patch) => setRows((r) => ({ ...r, [id]: { ...r[id], ...patch } }));
  const aiMap = Object.fromEntries((ai?.items || []).map((it) => [it.indicator_id, it]));

  const sumFor = (list) => list.reduce((acc, i) => acc + (Number(rows[i.id]?.score) || 0), 0);
  const umumSum = sumFor(inds.umum); const teknisSum = sumFor(inds.teknis);

  const runAi = async () => {
    setAiBusy(true);
    try {
      const { data } = await api.post(`/submissions/${activeId}/ai-recommend`);
      setAi(data);
      const n = data.items.filter((i) => i.kelas).length;
      toast.success(`Rekomendasi AI siap: ${n}/${data.items.length} indikator`);
    } catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail)); }
    setAiBusy(false);
  };
  const applyAi = () => {
    setRows((r) => {
      const next = { ...r };
      (ai?.items || []).forEach((it) => {
        if (it.kelas && it.score != null && next[it.indicator_id]) {
          next[it.indicator_id] = { ...next[it.indicator_id], kelas: it.kelas, score: it.score, data_validasi: next[it.indicator_id].data_validasi || String(it.data_value || "").replace(/[^0-9.,]/g, "").slice(0, 500) };
        }
      });
      return next;
    });
    toast.success("Rekomendasi AI diterapkan — silakan periksa & sesuaikan");
  };

  const submitScore = async () => {
    if (!allScored) return toast.error("Pilih skor untuk semua indikator");
    setSaving(true);
    try {
      const items = allInds.map((i) => ({ indicator_id: i.id, ok: rows[i.id].ok, note: rows[i.id].note, data_validasi: rows[i.id].data_validasi, kelas: rows[i.id].kelas || null, score: Number(rows[i.id].score) }));
      await api.post(`/submissions/${activeId}/score`, { items, overall_note: overallNote });
      toast.success("Penilaian selesai & dirilis"); setActiveId(null); await load();
    } catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail)); }
    setSaving(false);
  };

  const years = [...new Set(subs.map((s) => s.year))].sort((a, b) => b - a);
  const byYear = useCallback((list) => yearFilter === "all" ? list : list.filter((s) => String(s.year) === String(yearFilter)), [yearFilter]);
  const queue = useMemo(() => byYear(subs.filter((s) => s.status === "menunggu_penilaian")), [subs, byYear]);
  const done = useMemo(() => byYear(subs.filter((s) => s.status === "selesai")), [subs, byYear]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar period={period} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {!active ? (
          <>
            <div className="mb-8"><h1 className="font-display text-2xl sm:text-3xl font-extrabold text-slate-900 flex items-center gap-2"><ClipboardCheck className="w-7 h-7 text-emerald-600" /> Dashboard Penilai</h1><p className="text-muted-foreground text-sm mt-1" data-testid="penilai-subtitle">Validasi berkas bukti dukung dan penilaian tipologi perangkat daerah.</p></div>
            <Tabs defaultValue="penilaian">
              <TabsList className="flex-wrap h-auto">
                <TabsTrigger value="penilaian" data-testid="tab-penilaian">Penilaian</TabsTrigger>
                <TabsTrigger value="rekap" data-testid="tab-rekap" className="gap-1.5"><BarChart3 className="w-4 h-4" /> Rekap Penilaian</TabsTrigger>
                <TabsTrigger value="laporan" data-testid="tab-laporan">Laporan Hasil</TabsTrigger>
              </TabsList>
              <TabsContent value="penilaian" className="mt-6">
                <div className="flex items-center gap-3 mb-4">
                  <Label className="text-xs text-muted-foreground">Filter Tahun</Label>
                  <Select value={yearFilter} onValueChange={setYearFilter}><SelectTrigger className="w-40" data-testid="year-filter"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">Semua Tahun</SelectItem>{years.map((y) => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}</SelectContent></Select>
                </div>
                <Tabs defaultValue="queue">
                  <TabsList><TabsTrigger value="queue" data-testid="tab-queue">Menunggu ({queue.length})</TabsTrigger><TabsTrigger value="done" data-testid="tab-done">Selesai ({done.length})</TabsTrigger></TabsList>
                  <TabsContent value="queue" className="mt-4"><SubmissionTable list={queue} mode="queue" action="Validasi & Nilai" onOpen={openScore} /></TabsContent>
                  <TabsContent value="done" className="mt-4"><SubmissionTable list={done} mode="done" action="Lihat Hasil" onOpen={openScore} /></TabsContent>
                </Tabs>
              </TabsContent>
              <TabsContent value="rekap" className="mt-6"><RekapPenilaian periodId={period?.id} /></TabsContent>
              <TabsContent value="laporan" className="mt-6"><ReportsPanel canManage={true} /></TabsContent>
            </Tabs>
          </>
        ) : (
          <div>
            <button data-testid="back-to-list" onClick={() => setActiveId(null)} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-slate-900 mb-4"><ArrowLeft className="w-4 h-4" /> Kembali ke daftar</button>
            <div className="flex flex-wrap items-start justify-between gap-3 mb-4"><div><h2 className="font-display text-2xl font-extrabold text-slate-900">{active.device_name}</h2><div className="text-sm text-muted-foreground">{active.area} · {active.urusan}{active.sub_urusan ? ` — ${active.sub_urusan}` : ""} · {active.year}</div>{active.scoring?.scored_at && <div className="text-xs text-muted-foreground mt-0.5">Dinilai: {fmtDateTime(active.scoring.scored_at)} oleh {active.scoring.penilai_name}</div>}</div><StatusPill status={active.status} /></div>
            {active.status === "selesai" ? (
              <div className="space-y-4">
                <BeritaAcaraButtons submissionId={active.id} />
                <SubmissionScoreView submission={active} />
              </div>
            ) : (
              <div className="space-y-3 max-w-5xl">
                <div className="rounded-2xl border border-violet-200 bg-violet-50/70 p-4 flex flex-wrap items-center justify-between gap-3" data-testid="ai-panel">
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-violet-700 mt-0.5" />
                    <div>
                      <div className="text-sm font-semibold text-violet-900">Bantuan Penilaian AI (Gemini 3.1 Pro)</div>
                      <div className="text-xs text-violet-800/80">AI membaca berkas bukti tiap indikator dan merekomendasikan skor. Rekomendasi bersifat awal — keputusan tetap pada Tim Penilai.</div>
                      {ai && <div className="text-[11px] text-violet-700 mt-1">Terakhir: {new Date(ai.at).toLocaleString("id-ID")} · {ai.items.filter((i) => i.kelas).length}/{ai.items.length} indikator terisi</div>}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" className="gap-2 border-violet-300 text-violet-800 hover:bg-violet-100" data-testid="ai-recommend-btn" disabled={aiBusy} onClick={runAi}>{aiBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} {ai ? "Analisis Ulang" : "Minta Rekomendasi AI"}</Button>
                    {ai && <Button className="gap-2 bg-violet-700 hover:bg-violet-800" data-testid="ai-apply-btn" onClick={applyAi}><Wand2 className="w-4 h-4" /> Terapkan Semua</Button>}
                  </div>
                </div>
                <div className="text-sm font-semibold text-slate-900">Faktor Umum (maks 200)</div>
                {inds.umum.map((ind) => <ScoreRow key={ind.id} ind={ind} row={rows[ind.id] || {}} upload={(active.uploads || {})[ind.id]} ai={aiMap[ind.id]} onChange={(p) => setRow(ind.id, p)} onOpenFile={openFile} />)}
                <div className="text-sm font-semibold text-slate-900 pt-2">Faktor Teknis (maks 800)</div>
                {inds.teknis.map((ind) => <ScoreRow key={ind.id} ind={ind} row={rows[ind.id] || {}} upload={(active.uploads || {})[ind.id]} ai={aiMap[ind.id]} onChange={(p) => setRow(ind.id, p)} onOpenFile={openFile} />)}
                <Textarea data-testid="overall-note-input" placeholder="Catatan/rekomendasi keseluruhan (opsional)" value={overallNote} onChange={(e) => setOverallNote(e.target.value)} rows={2} />
                <div className="sticky bottom-0 bg-background py-3 border-t flex flex-wrap items-center justify-between gap-3">
                  <div className="text-sm font-mono text-slate-700" data-testid="live-total">Umum <b>{umumSum}</b> + Teknis <b>{teknisSum}</b> = <span className="text-primary font-bold">{umumSum + teknisSum}</span></div>
                  <Button className="gap-2 h-11" data-testid="submit-score-btn" onClick={submitScore} disabled={saving || !allScored}><ClipboardCheck className="w-4 h-4" /> Finalisasi Penilaian</Button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
