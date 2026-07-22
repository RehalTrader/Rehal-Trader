const ACCESS_KEY = "tsp_access_token";
const REFRESH_KEY = "tsp_refresh_token";

export function setTokens(accessToken: string, refreshToken: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function getTokens(): { accessToken: string | null; refreshToken: string | null } {
  if (typeof window === "undefined") return { accessToken: null, refreshToken: null };
  return {
    accessToken: localStorage.getItem(ACCESS_KEY),
    refreshToken: localStorage.getItem(REFRESH_KEY),
  };
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isAuthenticated(): boolean {
  return !!getTokens().accessToken;
}
