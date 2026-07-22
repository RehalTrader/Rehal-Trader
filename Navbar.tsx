"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ThemeToggle } from "./ThemeToggle";
import { clearTokens, isAuthenticated } from "@/lib/auth";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const authed = isAuthenticated();

  function handleLogout() {
    clearTokens();
    router.push("/login");
  }

  const links = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/dashboard/history", label: "Signal History" },
    { href: "/admin", label: "Admin" },
  ];

  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between px-6 py-3 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur">
      <Link href="/" className="font-bold text-lg tracking-tight">
        Signal<span className="text-buy">AI</span>
      </Link>

      {authed && (
        <div className="hidden md:flex gap-6 text-sm">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={pathname === l.href ? "font-semibold text-buy" : "text-slate-500 hover:text-foreground"}
            >
              {l.label}
            </Link>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3">
        <ThemeToggle />
        {authed ? (
          <button onClick={handleLogout} className="text-sm px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700">
            Log out
          </button>
        ) : (
          <Link href="/login" className="text-sm px-3 py-1.5 rounded-lg bg-buy text-white">
            Log in
          </Link>
        )}
      </div>
    </nav>
  );
}
