interface Props {
  confidence: number; // 0-100
  direction: "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL";
}

const DIRECTION_COLOR: Record<Props["direction"], string> = {
  STRONG_BUY: "#15803d",
  BUY: "#16a34a",
  NEUTRAL: "#6b7280",
  SELL: "#dc2626",
  STRONG_SELL: "#b91c1c",
};

export function ConfidenceMeter({ confidence, direction }: Props) {
  const color = DIRECTION_COLOR[direction];
  const clamped = Math.max(0, Math.min(100, confidence));

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1 text-slate-500">
        <span>AI Confidence</span>
        <span className="font-semibold" style={{ color }}>
          {clamped.toFixed(0)}%
        </span>
      </div>
      <div className="w-full h-2.5 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${clamped}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
