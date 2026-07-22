import { render, screen } from "@testing-library/react";
import { ConfidenceMeter } from "@/components/ConfidenceMeter";
import { SignalCard } from "@/components/SignalCard";
import type { SignalOut } from "@/lib/api";

describe("ConfidenceMeter", () => {
  it("renders the confidence percentage", () => {
    render(<ConfidenceMeter confidence={82} direction="BUY" />);
    expect(screen.getByText("82%")).toBeInTheDocument();
  });

  it("clamps values above 100", () => {
    render(<ConfidenceMeter confidence={150} direction="STRONG_BUY" />);
    expect(screen.getByText("100%")).toBeInTheDocument();
  });
});

describe("SignalCard", () => {
  const mockSignal: SignalOut = {
    id: "1",
    symbol: "XAUUSD",
    asset_class: "gold",
    timeframe: "15m",
    direction: "STRONG_BUY",
    confidence: 88,
    entry_price: 2400.5,
    stop_loss: 2390.0,
    take_profit: 2420.0,
    candle_time: new Date().toISOString(),
    created_at: new Date().toISOString(),
  };

  it("renders symbol and direction label", () => {
    render(<SignalCard signal={mockSignal} />);
    expect(screen.getByText("XAUUSD")).toBeInTheDocument();
    expect(screen.getByText("STRONG BUY")).toBeInTheDocument();
  });

  it("renders entry, stop loss, and take profit values", () => {
    render(<SignalCard signal={mockSignal} />);
    expect(screen.getByText("2400.5")).toBeInTheDocument();
    expect(screen.getByText("2390")).toBeInTheDocument();
    expect(screen.getByText("2420")).toBeInTheDocument();
  });
});
