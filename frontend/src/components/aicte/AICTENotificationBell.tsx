import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Bell, AlertTriangle, CheckCircle, ExternalLink, ShieldAlert, ArrowRight } from 'lucide-react';
import { api } from '../../services/api';
import { AICTENotification } from '../../types';

interface UnreadCountData {
  unread_count: number;
  unacknowledged_count: number;
  critical_count: number;
}

export const AICTENotificationBell: React.FC = () => {
  const [counts, setCounts] = useState<UnreadCountData>({
    unread_count: 0,
    unacknowledged_count: 0,
    critical_count: 0,
  });
  const [previewItems, setPreviewItems] = useState<AICTENotification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchUnreadCounts = async () => {
    try {
      const data = await api.get<UnreadCountData>('/aicte/notifications/unread-count');
      setCounts(data);
    } catch {
      // Quiet background failure
    }
  };

  const fetchPreviewNotifications = async () => {
    setLoading(true);
    try {
      const res = await api.get<{ items: AICTENotification[] }>('/aicte/notifications?page=1&page_size=5&is_read=false');
      setPreviewItems(res.items || []);
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnreadCounts();
    const interval = setInterval(fetchUnreadCounts, 30000); // 30s poll
    return () => clearInterval(interval);
  }, []);

  const handleToggle = () => {
    if (!isOpen) {
      fetchPreviewNotifications();
    }
    setIsOpen(!isOpen);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkRead = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.post(`/aicte/notifications/${id}/read`);
      setPreviewItems((prev) => prev.filter((item) => item.id !== id));
      setCounts((prev) => ({
        ...prev,
        unread_count: Math.max(0, prev.unread_count - 1),
      }));
    } catch {
      // Ignore
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={handleToggle}
        className="relative p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        title="AICTE Alerts & Notifications"
        aria-label="AICTE Alerts & Notifications"
      >
        <Bell className="w-5 h-5" />
        {counts.unread_count > 0 && (
          <span
            className={`absolute -top-1 -right-1 flex items-center justify-center min-w-[20px] h-5 px-1 text-[11px] font-bold text-white rounded-full border-2 border-white shadow-sm ${
              counts.critical_count > 0 ? 'bg-red-600 animate-pulse' : 'bg-blue-600'
            }`}
          >
            {counts.unread_count > 99 ? '99+' : counts.unread_count}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-w-[90vw] bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm flex items-center gap-2">
                AICTE Alert Center
                {counts.critical_count > 0 && (
                  <span className="text-[10px] uppercase font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full border border-red-200">
                    {counts.critical_count} Critical
                  </span>
                )}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {counts.unread_count} unread alert{counts.unread_count === 1 ? '' : 's'}
              </p>
            </div>
            <Link
              to="/aicte/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 transition"
            >
              View All <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="max-h-[360px] overflow-y-auto divide-y divide-slate-100">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading alerts...</div>
            ) : previewItems.length === 0 ? (
              <div className="p-8 text-center">
                <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-slate-700">No active unread alerts</p>
                <p className="text-[11px] text-slate-400 mt-0.5">All monitored cases are within configured SLA targets</p>
              </div>
            ) : (
              previewItems.map((item) => (
                <div
                  key={item.id}
                  className={`p-3.5 hover:bg-slate-50 transition flex items-start gap-3 ${
                    item.severity === 'CRITICAL' ? 'bg-red-50/30' : ''
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {item.severity === 'CRITICAL' ? (
                      <ShieldAlert className="w-4 h-4 text-red-600" />
                    ) : item.severity === 'WARNING' ? (
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                    ) : (
                      <Bell className="w-4 h-4 text-blue-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        {item.category || item.notification_type}
                      </span>
                      <span className="text-[10px] text-slate-400 shrink-0">
                        {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <h4 className="text-xs font-semibold text-slate-800 truncate mt-0.5">{item.title}</h4>
                    <p className="text-[11px] text-slate-500 line-clamp-2 mt-0.5 leading-snug">{item.message}</p>
                    <div className="mt-2 flex items-center gap-2">
                      {item.link && (
                        <Link
                          to={item.link}
                          onClick={() => setIsOpen(false)}
                          className="text-[11px] font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1"
                        >
                          Action <ExternalLink className="w-3 h-3" />
                        </Link>
                      )}
                      <button
                        onClick={(e) => handleMarkRead(item.id, e)}
                        className="text-[11px] text-slate-400 hover:text-slate-600 transition"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-2.5 bg-slate-50 border-t border-slate-100 text-center">
            <Link
              to="/aicte/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs font-medium text-slate-600 hover:text-slate-900 transition block py-1"
            >
              Open Centralized AICTE Alert Hub →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
