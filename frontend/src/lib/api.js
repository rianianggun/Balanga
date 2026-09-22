import axios from "axios";

export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API, withCredentials: true });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function formatApiErrorDetail(detail) {
  if (detail == null) return "Terjadi kesalahan. Silakan coba lagi.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail
      .map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e)))
      .filter(Boolean)
      .join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

// Bangun URL endpoint file (Excel/PDF) yang membawa token via query string untuk dibuka di tab baru
export function authUrl(path, params = {}) {
  const token = localStorage.getItem("token");
  const qs = new URLSearchParams({ ...Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== "")), auth: token }).toString();
  return `${API}${path}?${qs}`;
}

// Buka berkas bukti dukung dalam pop-up pratinjau (tanpa unduh). Ditangani oleh <FilePreviewHost /> di App.
export function openFile(fileId, name) {
  window.dispatchEvent(new CustomEvent("balanga:preview", { detail: { fileId, name } }));
}

export function downloadSurat(submissionId) {
  window.open(authUrl(`/submissions/${submissionId}/surat-verifikasi`), "_blank", "noopener");
}
