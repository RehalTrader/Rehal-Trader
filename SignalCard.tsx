import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { ConfidenceMeter } from "./ConfidenceMeter";
import type { SignalOut } from "@/lib/api";

const DIRECTION_STYLES: Record<SignalOut["direction"], { bg: string; icon: JSX.Element; label: string }> = {
  STRONG_BUY: { bg: "bg-green-700/10 border-green-700/40", icon: <ArrowUpRight className="text-green-700" />, label: "STRONG BUY" },
  BUY: { bg: "bg-green-500/10 border-green-500/40", icon: <ArrowUpRight className="text-green-500" />, label: "BUY" },
  NEUTRAL: { bg: "bg-slate-500/10 border-slate-500/40", icon: <Minus className="text-slate-500" />, label: "NEUTRAL" },
  SELL: { bg: "bg-red-500/10 border-red-500/40", icon: <ArrowDownRight className="text-red-500" />, label: "SELL" },
  STRONG_SELL: { bg: "bg-red-700/10 border-red-700/40", icon: <ArrowDownRight className="text-red-700" />, label: "STRONG SELL" },
};

export function SignalCard({ signal }: { signal: SignalOut }) {
  const style = DIRECTION_STYLES[signal.direction];

  return (
    <div className={`rounded-xl border p-4 flex flex-col gap-3 ${style.bg}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {style.icon}
          <span className="font-semibold">{signal.symbol}</span>
          <span className="text-xs text-slate-500">{signal.timeframe}</span>
        </div>
        <span className="text-xs font-bold tracking-wide">{style.label}</span>
      </div>

      <ConfidenceMeter confidence={signal.confidence} direction={signal.direction} />

      <div className="grid grid-cols-3 gap-2 text-xs text-slate-500">
        <div>
          <div className="text-[10px] uppercase">Entry</div>
          <div className="font-medium text-foreground">{signal.entry_price}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase">Stop Loss</div>
          <div className="font-medium text-foreground">{signal.stop_loss}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase">Take Profit</div>
          <div className="font-medium text-foreground">{signal.take_profit}</div>
        </div>
      </div>

      <div className="text-[11px] text-slate-400">
        {new Date(signal.candle_time).toLocaleString()}
      </div>
    </div>
  );
}
