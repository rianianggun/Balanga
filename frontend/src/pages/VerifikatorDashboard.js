import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api, downloadSurat } from "../lib/api";
import { Navbar } from "../components/Navbar";
import { StatusPill } from "../components/StatusPill";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import { ShieldCheck, Eye, MapPin, FileBadge } from "lucide-react";

export default function VerifikatorDashboard() {
  const navigate = useNavigate();
  const [subs, setSubs] = useState([]);
  const [period, setPeriod] = useState(null);
  const [me, setMe] = useState(null);
  const [yearFilter, setYearFilter] = useState("all");

  const load = useCallback(async () => {
    const [s, p, m] = await Promise.all([api.get("/submissions"), api.get("/periods/active"), api.get("/auth/me")]);
    setSubs(s.data); setPeriod(p.data && p.data.id ? p.data : null); setMe(m.data);
  }, []);
  useEffect(() => { load(); }, [load]);

  const years = [...new Set(subs.map((s) => s.year))].sort((a, b) => b - a);
  const byYear = (list) => yearFilter === "all" ? list : list.filter((s) => String(s.year) === String(yearFilter));
  const queue = byYear(subs.filter((s) => s.status === "menunggu_verifikasi"));
  const approved = byYear(subs.filter((s) => ["menunggu_penilaian", "selesai"].includes(s.status)));
  const rejected = byYear(subs.filter((s) => s.status === "ditolak"));
  const fmt = (d) => d ? new Date(d).toLocaleString("id-ID", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "-";

  const Table = ({ list, showAcc }) => (
    <div className="rounded-2xl border border-border bg-white overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left text-xs text-muted-foreground"><tr><th className="px-4 py-3">Perangkat Daerah</th><th className="px-4 py-3">Urusan</th><th className="px-4 py-3">Pemohon</th><th className="px-4 py-3">Tahun</th>{showAcc ? <th className="px-4 py-3">Tanggal ACC</th> : <th className="px-4 py-3">Status</th>}<th className="px-4 py-3 text-right">Aksi</th></tr></thead>
        <tbody>
          {list.length === 0 && <tr><td colSpan={6} className="text-center py-12 text-muted-foreground">Tidak ada data.</td></tr>}
          {list.map((s) => (
            <tr key={s.id} data-testid={`verif-row-${s.id}`} className="border-t border-border">
              <td className="px-4 py-3 font-medium text-slate-800">{s.device_name}</td>
              <td className="px-4 py-3 text-xs text-muted-foreground">{s.urusan}{s.sub_urusan ? ` — ${s.sub_urusan}` : ""}</td>
              <td className="px-4 py-3 text-xs text-muted-foreground">{s.perangkat_name}</td>
              <td className="px-4 py-3">{s.year}</td>
              {showAcc ? <td className="px-4 py-3 text-xs text-emerald-700">{fmt(s.verification?.verified_at)}</td> : <td className="px-4 py-3"><StatusPill status={s.status} /></td>}
              <td className="px-4 py-3 text-right">
                <div className="inline-flex gap-2">
                  {showAcc && <Button variant="ghost" size="sm" className="gap-1.5 text-emerald-700" data-testid={`surat-btn-${s.id}`} onClick={() => downloadSurat(s.id)}><FileBadge className="w-4 h-4" /> Surat</Button>}
                  <Button variant="outline" size="sm" className="gap-1.5" data-testid={`review-btn-${s.id}`} onClick={() => navigate(`/verifikasi/${s.id}`)}><Eye className="w-4 h-4" /> {s.status === "menunggu_verifikasi" ? "Tinjau" : "Detail"}</Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      <Navbar period={period} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="mb-6"><h1 className="font-display text-2xl sm:text-3xl font-extrabold text-slate-900 flex items-center gap-2"><ShieldCheck className="w-7 h-7 text-amber-600" /> Dashboard Verifikator</h1><p className="text-muted-foreground text-sm mt-1 flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> Wilayah: <span className="font-semibold text-slate-700">{me?.area}</span> — hanya pengajuan area ini.</p></div>
        <div className="flex items-center gap-3 mb-4"><Label className="text-xs text-muted-foreground">Filter Tahun</Label><Select value={yearFilter} onValueChange={setYearFilter}><SelectTrigger className="w-40" data-testid="year-filter"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">Semua Tahun</SelectItem>{years.map((y) => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}</SelectContent></Select></div>
        <Tabs defaultValue="queue">
          <TabsList>
            <TabsTrigger value="queue" data-testid="tab-queue">Antrean ({queue.length})</TabsTrigger>
            <TabsTrigger value="approved" data-testid="tab-approved">Sudah Disetujui ({approved.length})</TabsTrigger>
            <TabsTrigger value="rejected" data-testid="tab-rejected">Dikembalikan ({rejected.length})</TabsTrigger>
          </TabsList>
          <TabsContent value="queue" className="mt-6"><Table list={queue} /></TabsContent>
          <TabsContent value="approved" className="mt-6"><Table list={approved} showAcc /></TabsContent>
          <TabsContent value="rejected" className="mt-6"><Table list={rejected} /></TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
