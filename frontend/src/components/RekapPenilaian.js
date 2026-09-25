import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { TipeBadge } from "./TipeSummary";
import { SearchBox } from "./TableTools";
import { Button } from "./ui/button";
import { Checkbox } from "./ui/checkbox";
import { Label } from "./ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./ui/dialog";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts";
import { CheckCircle2, Clock, MinusCircle, ListOrdered, MapPin } from "lucide-react";

const STATUS = {
  selesai: { label: "Semua dinilai", cls: "bg-emerald-100 text-emerald-800 border-emerald-300", Icon: CheckCircle2 },
  berjalan: { label: "Masih ada antrean", cls: "bg-amber-100 text-amber-800 border-amber-300", Icon: Clock },
  belum_ada: { label: "Belum ada pengajuan", cls: "bg-slate-100 text-slate-600 border-slate-300", Icon: MinusCircle },
};
const short = (a) => a.replace("Kabupaten ", "Kab. ").replace("Provinsi ", "Prov. ");

// Menu "Rekap Penilaian" (Penilai): progres per daerah, grafik, 5 teratas per daerah, rincian semua PD
export function RekapPenilaian({ periodId }) {
  const [areas, setAreas] = useState(null);
  const [mult, setMult] = useState(false);
  const [q, setQ] = useState("");
  const [detail, setDetail] = useState(null);
  const [onlyActive, setOnlyActive] = useState(true);
  const pengali = mult ? 1.1 : 1;
  useEffect(() => {
    api.get("/stats/rekap-penilaian", { params: { period_id: periodId || undefined, pengali } }).then((r) => setAreas(r.data)).catch(() => setAreas([]));
  }, [periodId, pengali]);

  const list = (areas || []).filter((a) => (!onlyActive || a.devices_total > 0) && (!q || a.area.toLowerCase().includes(q.toLowerCase())));
  const chart = (areas || []).filter((a) => a.devices_total > 0).map((a) => ({ area: short(a.area), Selesai: a.selesai, "Menunggu Penilaian": a.menunggu_penilaian, "Tipe A": a.counts.A, "Tipe B": a.counts.B, "Tipe C": a.counts.C }));
  const done = (areas || []).filter((a) => a.status === "selesai").length; const running = (areas || []).filter((a) => a.status === "berjalan").length;

  return (
    <div className="space-y-6" data-testid="rekap-penilaian">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[{ l: "Daerah selesai dinilai", v: done, c: "text-emerald-700" }, { l: "Daerah masih ada antrean", v: running, c: "text-amber-700" }, { l: "Daerah belum ada pengajuan", v: (areas || []).length - done - running, c: "text-slate-500" }].map((x) => (
          <div key={x.l} className="rounded-2xl border border-border bg-white p-4"><div className={`text-3xl font-display font-extrabold ${x.c}`}>{areas ? x.v : "-"}</div><div className="text-xs text-muted-foreground mt-1">{x.l}</div></div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div><div className="text-sm font-semibold text-slate-900">Grafik Perangkat Daerah per Kabupaten/Kota</div><div className="text-xs text-muted-foreground">Urusan selesai vs menunggu penilaian, serta sebaran tipe PD</div></div>
          <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-600"><Checkbox checked={mult} onCheckedChange={(v) => setMult(!!v)} data-testid="rekap-multiplier" /><Label className="cursor-pointer text-xs">Kalikan 1,1</Label></label>
        </div>
        {chart.length === 0 ? <div className="text-center py-12 text-sm text-muted-foreground">Belum ada data.</div> : (
          <ResponsiveContainer width="100%" height={Math.max(220, chart.length * 44)}>
            <BarChart data={chart} layout="vertical" margin={{ left: 30, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" horizontal={false} />
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} /><YAxis type="category" dataKey="area" width={130} tick={{ fontSize: 11 }} />
              <Tooltip /><Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Selesai" stackId="s" fill="#059669" /><Bar dataKey="Menunggu Penilaian" stackId="s" fill="#f59e0b" radius={[0, 4, 4, 0]} />
              <Bar dataKey="Tipe A" stackId="t" fill="#0d9488" /><Bar dataKey="Tipe B" stackId="t" fill="#34d399" /><Bar dataKey="Tipe C" stackId="t" fill="#d97706" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <SearchBox value={q} onChange={setQ} placeholder="Cari kabupaten/kota..." className="w-full sm:w-72" testId="rekap-search" />
        <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-600"><Checkbox checked={onlyActive} onCheckedChange={(v) => setOnlyActive(!!v)} data-testid="rekap-only-active" /><Label className="cursor-pointer text-xs">Hanya daerah dengan pengajuan</Label></label>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {list.map((a) => {
          const st = STATUS[a.status] || STATUS.belum_ada;
          return (
            <div key={a.area} className="rounded-2xl border border-border bg-white p-5" data-testid={`rekap-area-${a.area}`}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div><div className="font-display font-bold text-slate-900 flex items-center gap-1.5"><MapPin className="w-4 h-4 text-primary" /> {a.area}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{a.devices_total} perangkat daerah · {a.selesai} urusan selesai · {a.menunggu_penilaian} menunggu penilaian</div></div>
                <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${st.cls}`}><st.Icon className="w-3 h-3" /> {st.label}</span>
              </div>
              <div className="mt-3 h-2 rounded-full bg-muted overflow-hidden"><div className="h-full bg-emerald-500 transition-all" style={{ width: `${a.progress}%` }} /></div>
              <div className="text-[11px] text-muted-foreground mt-1">Progres penilaian {a.progress}%</div>
              <table className="w-full text-sm mt-3">
                <thead className="text-left text-[11px] text-muted-foreground border-b border-border"><tr><th className="py-1.5">#</th><th className="py-1.5">Perangkat Daerah</th><th className="py-1.5 text-right">Nilai Akhir</th><th className="py-1.5 text-center">Tipe</th></tr></thead>
                <tbody>
                  {a.devices.length === 0 && <tr><td colSpan={4} className="py-4 text-center text-xs text-muted-foreground">Belum ada PD selesai dinilai.</td></tr>}
                  {a.devices.slice(0, 5).map((d, i) => (
                    <tr key={d.device_name} className="border-b border-slate-100 last:border-0">
                      <td className="py-1.5 text-xs font-bold text-slate-500">{i + 1}</td>
                      <td className="py-1.5 text-slate-800">{d.device_name}<span className="text-[10px] text-muted-foreground ml-1">({d.urusan_count} urusan)</span></td>
                      <td className="py-1.5 text-right font-mono font-semibold text-primary">{d.final}</td>
                      <td className="py-1.5 text-center"><TipeBadge tipe={d.tipe} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {a.devices.length > 0 && <Button variant="ghost" size="sm" className="mt-2 gap-1.5 text-primary" data-testid={`rekap-detail-${a.area}`} onClick={() => setDetail(a)}><ListOrdered className="w-4 h-4" /> Rincian semua PD ({a.devices.length})</Button>}
            </div>
          );
        })}
        {areas && list.length === 0 && <div className="text-center py-12 text-sm text-muted-foreground xl:col-span-2">Tidak ada daerah yang cocok.</div>}
      </div>

      <Dialog open={!!detail} onOpenChange={(o) => !o && setDetail(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader><DialogTitle>Rincian Total Skor — {detail?.area}</DialogTitle><DialogDescription>Semua perangkat daerah yang telah selesai dinilai, terurut dari skor tertinggi{pengali === 1.1 ? " (×1,1)" : ""}.</DialogDescription></DialogHeader>
          <div className="max-h-[60vh] overflow-auto rounded-xl border border-border">
            <table className="w-full text-sm" data-testid="rekap-detail-table">
              <thead className="bg-muted/50 text-left text-xs text-muted-foreground sticky top-0"><tr><th className="px-3 py-2">#</th><th className="px-3 py-2">Perangkat Daerah</th><th className="px-3 py-2">Urusan</th><th className="px-3 py-2 text-right">F. Umum</th><th className="px-3 py-2 text-right">F. Teknis</th><th className="px-3 py-2 text-right">Total</th><th className="px-3 py-2 text-right">Akhir</th><th className="px-3 py-2 text-center">Tipe</th></tr></thead>
              <tbody>
                {(detail?.devices || []).map((d, i) => (
                  <tr key={d.device_name} className="border-t border-slate-100">
                    <td className="px-3 py-2 text-xs font-bold text-slate-500">{i + 1}</td>
                    <td className="px-3 py-2 font-medium text-slate-800">{d.device_name}</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">{d.urusan.join(", ")}</td>
                    <td className="px-3 py-2 text-right font-mono">{d.umum_total}</td><td className="px-3 py-2 text-right font-mono">{d.teknis_total}</td>
                    <td className="px-3 py-2 text-right font-mono">{d.total}</td><td className="px-3 py-2 text-right font-mono font-bold text-primary">{d.final}</td>
                    <td className="px-3 py-2 text-center"><TipeBadge tipe={d.tipe} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
