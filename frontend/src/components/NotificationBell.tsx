import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { AppNotification } from "../types";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    try {
      const [count, list] = await Promise.all([
        api.getUnreadNotificationCount(),
        api.listNotifications(false),
      ]);
      setUnread(count.count);
      setItems(list.slice(0, 20));
    } catch {
      /* ignore when logged out or offline */
    }
  }, []);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 30000);
    const onFocus = () => void refresh();
    window.addEventListener("focus", onFocus);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("focus", onFocus);
    };
  }, [refresh]);

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  async function handleOpen() {
    setOpen((v) => !v);
    if (!open) {
      setLoading(true);
      await refresh();
      setLoading(false);
    }
  }

  async function markRead(id: number) {
    await api.markNotificationRead(id);
    await refresh();
  }

  async function markAllRead() {
    await api.markAllNotificationsRead();
    await refresh();
  }

  return (
    <div className="notification-bell" ref={panelRef}>
      <button type="button" className="secondary notification-bell-btn" onClick={() => void handleOpen()}>
        اعلان‌ها
        {unread > 0 && <span className="notification-badge">{unread.toLocaleString("fa-IR")}</span>}
      </button>
      {open && (
        <div className="notification-panel">
          <div className="notification-panel-head">
            <strong>اعلان‌های درون‌برنامه</strong>
            {unread > 0 && (
              <button type="button" className="link-button" onClick={() => void markAllRead()}>
                همه خوانده
              </button>
            )}
          </div>
          {loading && <p className="muted">در حال بارگذاری...</p>}
          {!loading && items.length === 0 && <p className="muted">اعلانی نیست.</p>}
          <ul className="notification-list">
            {items.map((item) => {
              const adUrl = item.payload?.ad_url;
              return (
              <li key={item.id} className={item.read_at ? "read" : "unread"}>
                <button type="button" className="notification-item-btn" onClick={() => void markRead(item.id)}>
                  <strong>{item.title || "آگهی جدید"}</strong>
                  {item.body && <small>{item.body.split("\n")[0]}</small>}
                  {typeof adUrl === "string" && (
                    <a
                      href={adUrl}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(e) => e.stopPropagation()}
                    >
                      مشاهده آگهی
                    </a>
                  )}
                </button>
              </li>
            );})}
          </ul>
        </div>
      )}
    </div>
  );
}
