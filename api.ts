import axios, { AxiosError, AxiosInstance } from "axios";
import { getTokens, setTokens, clearTokens } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const { accessToken } = getTokens();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let isRefreshing = false;
let queue: Array<() => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as any;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const { refreshToken } = getTokens();
      if (!refreshToken) {
        clearTokens();
        return Promise.reject(error);
      }

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          setTokens(data.access_token, data.refresh_token);
          queue.forEach((cb) => cb());
          queue = [];
        } catch {
          clearTokens();
          window.location.href = "/login";
        } finally {
          isRefreshing = false;
        }
      }

      return new Promise((resolve) => {
        queue.push(() => resolve(api(original)));
      });
    }

    return Promise.reject(error);
  }
);

// ---- Typed API calls ----
export interface SignalOut {
  id: string;
  symbol: string;
  asset_class: "forex" | "gold" | "crypto" | "indices";
  timeframe: string;
  direction: "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL";
  confidence: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  candle_time: string;
  created_at: string;
}

export async function fetchSignals(params: {
  symbol?: string;
  asset_class?: string;
  timeframe?: string;
  limit?: number;
}): Promise<SignalOut[]> {
  const { data } = await api.get<SignalOut[]>("/signals/", { params });
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function register(email: string, full_name: string, password: string) {
  const { data } = await api.post("/auth/register", { email, full_name, password });
  return data;
}

export async function fetchCurrentUser() {
  const { data } = await api.get("/users/me");
  return data;
}
