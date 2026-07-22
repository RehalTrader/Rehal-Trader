"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface NewsItem {
  time: string;
  currency: string;
  impact: "low" | "medium" | "high";
  event: string;
  actual?: string;
  forecast?: string;
  previous?: string;
}

const IMPACT_COLOR: Record<NewsItem["impact"], string> = {
  low: "bg-slate-400",
  medium: "bg-amber-500",
  high: "bg-red-600",
};

export function NewsPanel() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/market/news")
      .then((res) => setItems(res.data))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-4">
      <h3 className="font-semibold mb-3">Economic News</h3>

      {loading && <div className="text-sm text-slate-500">Loading calendar…</div>}
      {!loading && items.length === 0 && (
        <div className="text-sm text-slate-500">No high-impact events in range.</div>
      )}

      <ul className="flex flex-col gap-2 max-h-80 overflow-y-auto">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-center gap-2 text-sm border-b border-slate-100 dark:border-slate-800 pb-2">
            <span className={`w-2 h-2 rounded-full ${IMPACT_COLOR[item.impact]}`} />
            <span className="text-xs text-slate-500 w-14 shrink-0">{item.time}</span>
            <span className="text-xs font-semibold w-10 shrink-0">{item.currency}</span>
            <span className="flex-1 truncate">{item.event}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
