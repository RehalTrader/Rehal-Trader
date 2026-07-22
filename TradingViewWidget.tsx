"use client";

import { useEffect, useRef } from "react";

interface Props {
  symbol?: string;
  theme?: "light" | "dark";
  height?: number;
}

/**
 * Embeds TradingView's Advanced Real-Time Chart widget via their public embed script.
 * No API key required for the free embed; for production-grade data licensing see
 * TradingView's Charting Library / Trading Terminal products instead.
 */
export function TradingViewWidget({ symbol = "OANDA:XAUUSD", theme = "dark", height = 520 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.innerHTML = "";

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol,
      interval: "15",
      timezone: "Etc/UTC",
      theme,
      style: "1",
      locale: "en",
      enable_publishing: false,
      allow_symbol_change: true,
      support_host: "https://www.tradingview.com",
    });

    containerRef.current.appendChild(script);
  }, [symbol, theme]);

  return (
    <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800" style={{ height }}>
      <div className="tradingview-widget-container h-full" ref={containerRef}>
        <div className="tradingview-widget-container__widget h-full" />
      </div>
    </div>
  );
}
