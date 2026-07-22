import type { Metadata } from "next";
import "@/styles/globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "SignalAI — AI Trading Signals",
  description: "AI-powered trading signals for Forex, Gold, Crypto, and Indices.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider>
          <Navbar />
          <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
