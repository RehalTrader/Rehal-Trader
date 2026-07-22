"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, register } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      await register(email, fullName, password);
      await login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto mt-16 p-8 rounded-2xl border border-slate-200 dark:border-slate-800">
      <h1 className="text-2xl font-bold mb-6">Create your account</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="text-sm text-slate-500">Full name</label>
          <input
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-transparent"
          />
        </div>

        <div>
          <label className="text-sm text-slate-500">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-transparent"
          />
        </div>

        <div>
          <label className="text-sm text-slate-500">Password</label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-transparent"
          />
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="mt-2 py-2.5 rounded-lg bg-buy text-white font-medium disabled:opacity-50"
        >
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="text-sm text-slate-500 mt-6 text-center">
        Already have an account?{" "}
        <Link href="/login" className="text-buy font-medium">
          Log in
        </Link>
      </p>
    </div>
  );
}
