import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { TIPE_META } from "../lib/constants";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, LabelList } from "recharts";
import { Trophy } from "lucide-react";

export function TipeBadge({ tipe }) {
  const m = TIPE_META[tipe?.key] || { label: tipe?.label || "-", cls: "bg-slate-100 text-slate-600 border-slate-300" };
  return <span className={`px-2.5 py-1 rounded-full text-xs font-bold border whitespace-nowrap ${m.cls}`}>{m.label}</span>;
}

const COLORS = { A: "#0d9488", B: "#059669", C: "#d97706", Lainnya: "#94a3b8" };

// Grafik jumlah perangkat daerah per Tipe A/B/C + tabel 5 peringkat teratas
export function TipeSummary({ periodId, pengali = 1, title = "Ringkasan Tipologi Perangkat Daerah" }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.get("/stats/tipe-summary", { params: { period_id: periodId || undefined, pengali } }).then((r) => setData(r.data)).catch(() => setData({ counts: {}, ranking: [] }));
  }, [periodId, pengali]);
  const counts = data?.counts || {};
  const chart = ["A", "B", "C", "Lainnya"].map((k) => ({ tipe: k === "Lainnya" ? "Lainnya" : `Tipe ${k}`, key: k, jumlah: counts[k] || 0 }));
  const top5 = (data?.ranking || []).slice(0, 5);
  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4" data-testid="tipe-summary">
      <div className="lg:col-span-2 rounded-2xl border border-border bg-white p-5">
        <div className="text-sm font-semibold text-slate-900">{title}</div>
        <div className="text-xs text-muted-foreground mb-3">Jumlah perangkat daerah per tipe · total {data?.total_devices ?? 0} PD selesai dinilai</div>
        {!data ? <div className="h-56 animate-pulse bg-muted/40 rounded-xl" /> : (
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={chart} margin={{ top: 16, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="tipe" tick={{ fontSize: 12 }} /><YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip cursor={{ fill: "#f8fafc" }} />
              <Bar dataKey="jumlah" name="Jumlah PD" radius={[6, 6, 0, 0]}>
                {chart.map((c) => <Cell key={c.key} fill={COLORS[c.key]} />)}
                <LabelList dataKey="jumlah" position="top" style={{ fontSize: 12, fontWeight: 700, fill: "#0f172a" }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      <div className="lg:col-span-3 rounded-2xl border border-border bg-white p-5">
        <div className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Trophy className="w-4 h-4 text-amber-500" /> 5 Peringkat Skor Tertinggi</div>
        <div className="text-xs text-muted-foreground mb-3">Nilai akhir gabungan seluruh urusan per perangkat daerah{pengali === 1.1 ? " · ×1,1" : ""}</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="top5-table">
            <thead className="text-left text-xs text-muted-foreground border-b border-border"><tr><th className="py-2 pr-2">#</th><th className="py-2 pr-2">Perangkat Daerah</th><th className="py-2 pr-2">Kab/Kota</th><th className="py-2 pr-2 text-center">Urusan</th><th className="py-2 pr-2 text-right">Nilai Akhir</th><th className="py-2 text-center">Tipe</th></tr></thead>
            <tbody>
              {top5.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-muted-foreground">Belum ada perangkat daerah selesai dinilai.</td></tr>}
              {top5.map((d) => (
                <tr key={`${d.area}-${d.device_name}`} className="border-b border-slate-100 last:border-0" data-testid={`top5-row-${d.rank}`}>
                  <td className="py-2.5 pr-2"><span className={`inline-flex w-6 h-6 rounded-full items-center justify-center text-xs font-bold ${d.rank === 1 ? "bg-amber-100 text-amber-700" : d.rank === 2 ? "bg-slate-200 text-slate-700" : d.rank === 3 ? "bg-orange-100 text-orange-700" : "bg-muted text-slate-600"}`}>{d.rank}</span></td>
                  <td className="py-2.5 pr-2 font-medium text-slate-800">{d.device_name}</td>
                  <td className="py-2.5 pr-2 text-xs text-muted-foreground">{d.area.replace("Kabupaten ", "Kab. ").replace("Provinsi ", "Prov. ")}</td>
                  <td className="py-2.5 pr-2 text-center text-xs">{d.urusan_count}</td>
                  <td className="py-2.5 pr-2 text-right font-mono font-bold text-primary">{d.final}</td>
                  <td className="py-2.5 text-center"><TipeBadge tipe={d.tipe} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
