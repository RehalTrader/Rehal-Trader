"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "./auth";
import { fetchCurrentUser } from "./api";

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin";
  subscription_plan: "free" | "basic" | "pro" | "enterprise";
}

/** Redirects to /login if not authenticated; otherwise loads and returns the current user. */
export function useRequireAuth() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser()
      .then(setUser)
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  return { user, loading };
}
