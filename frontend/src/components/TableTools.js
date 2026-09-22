import React, { useMemo, useState } from "react";
import { Input } from "./ui/input";
import { Search, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

function getVal(obj, key) {
  if (typeof key === "function") return key(obj);
  return key.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);
}

// Hook: pencarian + pengurutan untuk daftar apa pun.
// keys: { kolom: accessor } — accessor berupa path string ("scoring.total") atau fungsi.
export function useTableTools(list, keys, defaultSort = { key: null, dir: "desc" }) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState(defaultSort);
  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    let out = list;
    if (q) {
      out = list.filter((item) => Object.values(keys).some((acc) => String(getVal(item, acc) ?? "").toLowerCase().includes(q)));
    }
    if (sort.key && keys[sort.key]) {
      const acc = keys[sort.key];
      out = [...out].sort((a, b) => {
        const va = getVal(a, acc); const vb = getVal(b, acc);
        if (va == null && vb == null) return 0;
        if (va == null) return 1;
        if (vb == null) return -1;
        const na = Number(va); const nb = Number(vb);
        const cmp = !isNaN(na) && !isNaN(nb) && va !== "" && vb !== "" ? na - nb : String(va).localeCompare(String(vb), "id");
        return sort.dir === "asc" ? cmp : -cmp;
      });
    }
    return out;
  }, [list, keys, query, sort]);
  const toggleSort = (key) => setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));
  return { query, setQuery, sort, toggleSort, rows };
}

export function SearchBox({ value, onChange, placeholder = "Cari...", className = "", testId = "search-input" }) {
  return (
    <div className={`relative ${className}`}>
      <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
      <Input className="pl-9 h-10" placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} data-testid={testId} />
    </div>
  );
}

// Header kolom yang bisa diklik untuk mengurutkan.
export function SortTh({ label, sortKey, sort, onSort, className = "", align = "left" }) {
  const active = sort.key === sortKey;
  const Icon = active ? (sort.dir === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
  return (
    <th className={`px-4 py-3 ${className}`}>
      <button type="button" onClick={() => onSort(sortKey)} data-testid={`sort-${sortKey}`}
        className={`inline-flex items-center gap-1 hover:text-slate-900 transition-colors ${align === "right" ? "flex-row-reverse" : ""} ${active ? "text-slate-900 font-semibold" : ""}`}>
        {label} <Icon className={`w-3.5 h-3.5 ${active ? "text-primary" : "opacity-50"}`} />
      </button>
    </th>
  );
}

export const fmtDateTime = (d) => d ? new Date(d).toLocaleString("id-ID", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "-";

// Waktu unggah terakhir dari peta uploads sebuah pengajuan
export const lastUploadAt = (s) => {
  if (s.last_upload_at) return s.last_upload_at;
  const ts = Object.values(s.uploads || {}).map((u) => u?.uploaded_at).filter(Boolean).sort();
  return ts.length ? ts[ts.length - 1] : null;
};
