import React from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Checkbox } from "./ui/checkbox";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "./ui/select";
import { FileText, Sparkles } from "lucide-react";

const KELAS = ["a", "b", "c", "d", "e"];

export function ScoreRow({ ind, row, upload, ai, onChange, onOpenFile }) {
  const scores = ind.scores || null;
  // Penilai memilih ANGKA skor langsung dari deretan skor; kelas (a-e) diturunkan otomatis dari posisi angka
  const pickScore = (val) => { const idx = scores.findIndex((s) => String(s) === String(val)); onChange({ kelas: idx >= 0 ? KELAS[idx] : null, score: scores[idx] }); };
  const pickKelas = (k) => onChange({ kelas: k, score: scores[KELAS.indexOf(k)] });
  return (
    <div className="rounded-xl border border-border p-4 space-y-3 bg-white" data-testid={`score-card-${ind.id}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-slate-900">{ind.order}. {ind.name}</div>
          {scores && <div className="text-[11px] text-muted-foreground mt-0.5 font-mono">Deretan skor: {scores.join(" · ")}</div>}
        </div>
        {upload && <Button variant="ghost" size="sm" className="gap-1.5 shrink-0 text-emerald-700" data-testid={`penilai-view-file-${ind.id}`} onClick={() => onOpenFile(upload.file_id, upload.original_filename)}><FileText className="w-4 h-4" /> Berkas</Button>}
      </div>
      {ai && (
        <div className={`rounded-lg px-3 py-2 text-xs flex flex-wrap items-center justify-between gap-2 ${ai.kelas ? "bg-violet-50 border border-violet-200 text-violet-900" : "bg-slate-50 border border-border text-slate-600"}`} data-testid={`ai-hint-${ind.id}`}>
          <div className="flex items-start gap-2 min-w-0">
            <Sparkles className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            <div>
              {ai.kelas ? <span className="font-semibold">Rekomendasi AI: skor {ai.score}</span> : <span className="font-semibold">AI: tidak ada rekomendasi</span>}
              {ai.data_value && <span> · Data: {ai.data_value}</span>}
              {ai.reason && <div className="text-[11px] opacity-80 mt-0.5">{ai.reason}</div>}
            </div>
          </div>
          {ai.kelas && scores && <Button size="sm" variant="outline" className="h-7 text-[11px] border-violet-300" data-testid={`ai-apply-${ind.id}`} onClick={() => pickKelas(ai.kelas)}>Pakai</Button>}
        </div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center">
        <label className="sm:col-span-2 flex items-center gap-2 cursor-pointer"><Checkbox checked={row.ok} onCheckedChange={(v) => onChange({ ok: !!v })} data-testid={`ok-${ind.id}`} /><span className="text-xs font-medium text-slate-600">Oke</span></label>
        <Input className="sm:col-span-3" inputMode="numeric" maxLength={500} placeholder="Data Hasil Validasi (angka)" data-testid={`validasi-${ind.id}`} value={row.data_validasi || ""} onChange={(e) => onChange({ data_validasi: e.target.value.replace(/[^0-9.,]/g, "").slice(0, 500) })} />
        <Input className="sm:col-span-4" placeholder="Catatan (opsional)" data-testid={`note-${ind.id}`} value={row.note || ""} onChange={(e) => onChange({ note: e.target.value })} />
        {scores ? (
          <Select value={row.score === "" || row.score == null ? "" : String(row.score)} onValueChange={pickScore}>
            <SelectTrigger className="sm:col-span-3 font-mono" data-testid={`kelas-${ind.id}`}><SelectValue placeholder="Pilih skor" /></SelectTrigger>
            <SelectContent>{scores.map((s, i) => <SelectItem key={`${s}-${i}`} value={String(s)} className="font-mono" data-testid={`kelas-${ind.id}-${KELAS[i]}`}>{s}</SelectItem>)}</SelectContent>
          </Select>
        ) : (
          <Input className="sm:col-span-3" type="number" min={0} max={1000} placeholder="Skor" data-testid={`score-${ind.id}`} value={row.score ?? ""} onChange={(e) => onChange({ score: e.target.value })} />
        )}
      </div>
    </div>
  );
}
