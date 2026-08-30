import type {
  AdFilterInput,
  AuthResponse,
  DataPreview,
  DataStatus,
  RefreshResponse,
  Search,
  SearchInput,
  User,
} from "../types";

const TOKEN_KEY = "bama_token";
const USER_KEY = "bama_user";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let message = "Request failed";
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const authStorage = {
  save(auth: AuthResponse) {
    localStorage.setItem(TOKEN_KEY, auth.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(auth.user));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  getUser(): User | null {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  },
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },
};

export const api = {
  register(email: string, password: string, fullName?: string) {
    return request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName || null }),
    });
  },
  login(email: string, password: string) {
    return request<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  me() {
    return request<User>("/api/auth/me");
  },
  listSearches() {
    return request<Search[]>("/api/searches");
  },
  createSearch(data: SearchInput) {
    return request<Search>("/api/searches", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
  updateSearch(id: number, data: SearchInput) {
    return request<Search>(`/api/searches/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },
  deleteSearch(id: number) {
    return request<void>(`/api/searches/${id}`, { method: "DELETE" });
  },
  toggleSearch(id: number) {
    return request<Search>(`/api/searches/${id}/toggle`, { method: "PATCH" });
  },
  previewAds(filter: AdFilterInput) {
    return request<DataPreview>("/api/ads/preview", {
      method: "POST",
      body: JSON.stringify(filter),
    });
  },
  getSearchResults(searchId: number) {
    return request<DataPreview>(`/api/searches/${searchId}/results`);
  },
  refreshData() {
    return request<RefreshResponse>("/api/crawl/refresh", { method: "POST" });
  },
  getDataStatus() {
    return request<DataStatus>("/api/data/status");
  },
};

export { ApiError, request };
