import React, { useState } from "react";
import { authUrl } from "../lib/api";
import { Button } from "./ui/button";
import { Checkbox } from "./ui/checkbox";
import { Label } from "./ui/label";
import { FileSpreadsheet, FileText, FileType2 } from "lucide-react";

// Unduh Berita Acara Verifikasi (Format Scoring) untuk satu pengajuan yang selesai dinilai
export function BeritaAcaraButtons({ submissionId, compact = false }) {
  const [mult, setMult] = useState(false);
  const pengali = mult ? 1.1 : 1;
  const open = (format) => window.open(authUrl(`/submissions/${submissionId}/berita-acara`, { format, pengali }), "_blank", "noopener");
  return (
    <div className={`flex flex-wrap items-center gap-2 ${compact ? "" : "rounded-xl border border-border bg-white px-4 py-3"}`} data-testid="berita-acara-panel">
      {!compact && <div className="text-sm font-semibold text-slate-800 mr-2">Berita Acara Verifikasi (Format Scoring)</div>}
      <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-600">
        <Checkbox checked={mult} onCheckedChange={(v) => setMult(!!v)} data-testid="ba-multiplier-checkbox" /> <Label className="cursor-pointer text-xs">Kalikan 1,1</Label>
      </label>
      <Button variant="outline" size="sm" className="gap-1.5 text-blue-800 border-blue-300 hover:bg-blue-50" data-testid="ba-word-btn" onClick={() => open("docx")}><FileType2 className="w-4 h-4" /> Word</Button>
      <Button variant="outline" size="sm" className="gap-1.5 text-emerald-700 border-emerald-300 hover:bg-emerald-50" data-testid="ba-excel-btn" onClick={() => open("xlsx")}><FileSpreadsheet className="w-4 h-4" /> Excel</Button>
      <Button variant="outline" size="sm" className="gap-1.5 text-red-700 border-red-300 hover:bg-red-50" data-testid="ba-pdf-btn" onClick={() => open("pdf")}><FileText className="w-4 h-4" /> PDF</Button>
    </div>
  );
}

// Tombol unduh Laporan Hasil (Word) untuk satu urusan/pengajuan dengan pengali mengikuti laporan
export function WordDownloadButton({ submissionId, applyMultiplier, testId }) {
  const open = () => window.open(authUrl(`/submissions/${submissionId}/berita-acara`, { format: "docx", pengali: applyMultiplier ? 1.1 : 1 }), "_blank", "noopener");
  return (
    <Button variant="outline" size="sm" className="gap-1.5 text-blue-800 border-blue-300 hover:bg-blue-50 h-7 px-2 text-xs" data-testid={testId || `word-btn-${submissionId}`} onClick={open}><FileType2 className="w-3.5 h-3.5" /> Word</Button>
  );
}
