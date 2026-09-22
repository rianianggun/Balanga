import React, { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { Bell, AlertTriangle, Info, AlertCircle, CheckCircle2, CalendarClock } from "lucide-react";
import { Popover, PopoverTrigger, PopoverContent } from "./ui/popover";

const ICON = { info: Info, warning: AlertTriangle, urgent: AlertCircle, success: CheckCircle2 };
const CLS = {
  info: "text-blue-700 bg-blue-50 border-blue-200",
  warning: "text-amber-700 bg-amber-50 border-amber-200",
  urgent: "text-red-700 bg-red-50 border-red-200",
  success: "text-emerald-700 bg-emerald-50 border-emerald-200",
};
const fmt = (d) => d ? new Date(d).toLocaleString("id-ID", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) : "";

function Item({ n }) {
  const Icon = ICON[n.level] || Info;
  return (
    <div data-testid={`notif-${n.level}`} className={`text-xs rounded-lg border px-3 py-2 flex gap-2 ${CLS[n.level] || CLS.info} ${n.kind === "event" && !n.read ? "ring-2 ring-offset-1 ring-primary/40" : ""}`}>
      <Icon className="w-4 h-4 shrink-0 mt-0.5" />
      <div className="min-w-0"><div>{n.message}</div>{n.created_at && <div className="text-[10px] opacity-70 mt-0.5">{fmt(n.created_at)}</div>}</div>
    </div>
  );
}

export function NotificationBell() {
  const [items, setItems] = useState([]);
  const load = useCallback(() => api.get("/notifications").then((r) => setItems(r.data)).catch(() => {}), []);
  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t); }, [load]);

  const events = items.filter((i) => i.kind === "event");
  const periodNotes = items.filter((i) => i.kind !== "event");
  const unread = events.filter((i) => !i.read).length;
  const urgent = periodNotes.some((i) => i.level === "urgent" || i.level === "warning");

  const onOpen = async (open) => {
    if (open && unread > 0) {
      try { await api.post("/notifications/read-all"); } catch (e) { /* ignore */ }
      setTimeout(() => setItems((it) => it.map((n) => ({ ...n, read: true }))), 1500);
    }
  };

  return (
    <Popover onOpenChange={onOpen}>
      <PopoverTrigger asChild>
        <button data-testid="notification-bell" className="relative w-10 h-10 rounded-full hover:bg-muted flex items-center justify-center transition-colors">
          <Bell className="w-5 h-5 text-slate-600" />
          {unread > 0 ? (
            <span data-testid="notification-unread-badge" className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">{unread > 9 ? "9+" : unread}</span>
          ) : items.length > 0 && (
            <span className={`absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full ${urgent ? "bg-red-500" : "bg-emerald-500"}`} />
          )}
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-96 p-3">
        <div className="font-display font-bold text-sm mb-2 text-slate-900 flex items-center justify-between">Pemberitahuan {unread > 0 && <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-100 text-red-700">{unread} baru</span>}</div>
        <div className="space-y-2 max-h-[60vh] overflow-auto pr-1">
          {events.length > 0 && <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Status pengajuan</div>}
          {events.map((n) => <Item key={n.id} n={n} />)}
          {periodNotes.length > 0 && <div className="text-[10px] uppercase tracking-widest text-muted-foreground flex items-center gap-1 pt-1"><CalendarClock className="w-3 h-3" /> Periode evaluasi</div>}
          {periodNotes.map((n) => <Item key={n.id} n={n} />)}
          {items.length === 0 && <div className="text-sm text-muted-foreground py-4 text-center">Tidak ada pemberitahuan.</div>}
        </div>
      </PopoverContent>
    </Popover>
  );
}
