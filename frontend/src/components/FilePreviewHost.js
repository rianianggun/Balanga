import React, { useEffect, useState } from "react";
import { api, formatApiErrorDetail } from "../lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./ui/dialog";
import { Button } from "./ui/button";
import { ExternalLink, Download, Loader2, FileWarning } from "lucide-react";
import { toast } from "sonner";

export const PREVIEW_EVENT = "balanga:preview";

// Global host: listens for `balanga:preview` events (dispatched by openFile in lib/api.js)
// and shows the file inline in a dialog (PDF/gambar) tanpa mengunduh.
export function FilePreviewHost() {
  const [file, setFile] = useState(null); // { fileId, name }
  const [blob, setBlob] = useState(null); // { url, type }
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handler = (e) => setFile({ fileId: e.detail.fileId, name: e.detail.name || "Berkas" });
    window.addEventListener(PREVIEW_EVENT, handler);
    return () => window.removeEventListener(PREVIEW_EVENT, handler);
  }, []);

  useEffect(() => {
    if (!file) return;
    let url;
    setLoading(true); setBlob(null);
    api.get(`/files/${file.fileId}/download`, { responseType: "blob" })
      .then((res) => {
        const type = res.data.type || res.headers["content-type"] || "application/octet-stream";
        url = URL.createObjectURL(res.data.slice(0, res.data.size, type));
        setBlob({ url, type });
      })
      .catch((e) => { toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Berkas tidak dapat dibuka"); setFile(null); })
      .finally(() => setLoading(false));
    return () => { if (url) setTimeout(() => URL.revokeObjectURL(url), 30000); };
  }, [file]);

  const isPdf = blob?.type?.includes("pdf");
  const isImg = blob?.type?.startsWith("image/");
  const openTab = () => blob && window.open(blob.url, "_blank", "noopener");
  const download = () => {
    if (!blob) return;
    const a = document.createElement("a"); a.href = blob.url; a.download = file?.name || "berkas"; a.click();
  };

  return (
    <Dialog open={!!file} onOpenChange={(o) => !o && setFile(null)}>
      <DialogContent className="max-w-5xl w-[96vw] h-[90vh] flex flex-col p-0 gap-0 overflow-hidden" data-testid="file-preview-dialog">
        <DialogHeader className="px-5 py-3 border-b border-border flex-row items-center justify-between gap-3 space-y-0">
          <div className="min-w-0">
            <DialogTitle className="text-base truncate" data-testid="file-preview-title">{file?.name}</DialogTitle>
            <DialogDescription className="text-xs">Pratinjau berkas bukti dukung — tidak diunduh otomatis.</DialogDescription>
          </div>
          <div className="flex gap-2 shrink-0 mr-6">
            <Button variant="outline" size="sm" className="gap-1.5" data-testid="file-preview-open-tab" disabled={!blob} onClick={openTab}><ExternalLink className="w-4 h-4" /> Buka di Tab Baru</Button>
            <Button variant="ghost" size="sm" className="gap-1.5" data-testid="file-preview-download" disabled={!blob} onClick={download}><Download className="w-4 h-4" /> Unduh</Button>
          </div>
        </DialogHeader>
        <div className="flex-1 bg-slate-100 min-h-0 flex items-center justify-center">
          {loading && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-5 h-5 animate-spin" /> Memuat berkas...</div>}
          {!loading && blob && isPdf && <iframe title="Pratinjau PDF" src={`${blob.url}#toolbar=1&view=FitH`} className="w-full h-full border-0" data-testid="file-preview-iframe" />}
          {!loading && blob && isImg && <img alt={file?.name} src={blob.url} className="max-w-full max-h-full object-contain" data-testid="file-preview-image" />}
          {!loading && blob && !isPdf && !isImg && (
            <div className="text-center p-8 max-w-md" data-testid="file-preview-unsupported">
              <FileWarning className="w-10 h-10 text-amber-500 mx-auto mb-3" />
              <div className="font-semibold text-slate-800">Pratinjau tidak tersedia untuk format ini</div>
              <p className="text-sm text-muted-foreground mt-1">Berkas Word/Excel tidak dapat ditampilkan langsung oleh browser. Gunakan tombol &quot;Buka di Tab Baru&quot; atau &quot;Unduh&quot;.</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
