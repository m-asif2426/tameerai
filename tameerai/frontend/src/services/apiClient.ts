/**
 * TameerAI - Centralized API Client (Phase 03.4B2)
 *
 * Implements:
 * - Environment-aware base URL resolution (Local vs Staging vs Production)
 * - Dual-token authentication with HttpOnly cookie support (credentials: "include")
 * - Automatic 401 refresh token rotation interceptor
 * - Standardized JSON error parsing and typed responses
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const USER_CACHE_KEY = "tameerai_user";

export interface ApiUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  phone?: string | null;
  city?: string | null;
  is_verified?: boolean;
  pec_number?: string | null;
  company?: string | null;
  bio?: string | null;
}

export interface AuthTokens {
  access_token?: string;
  accessToken?: string;
  token_type?: string;
  tokenType?: string;
  expires_in?: number;
  expiresIn?: number;
  refresh_token?: string;
  refreshToken?: string;
  user: ApiUser;
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
  skipAuthRefresh?: boolean;
}

class ApiClient {
  private baseURL: string;
  private isRefreshing: boolean = false;
  private refreshSubscribers: ((token: string) => void)[] = [];
  private inMemoryToken: string | null = null;
  private refreshPromise: Promise<string | null> | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  // Token & Cache Management (Exclusively in-memory; refresh token in Secure HttpOnly cookie)
  public getToken(): string | null {
    return this.inMemoryToken;
  }

  public setToken(token: string): void {
    this.inMemoryToken = token;
  }

  public clearAuth(): void {
    this.inMemoryToken = null;
    if (typeof window !== "undefined") {
      // Purge non-sensitive user metadata and sanitize any legacy tokens
      localStorage.removeItem(USER_CACHE_KEY);
      localStorage.removeItem("tameerai_access_token");
      localStorage.removeItem("tameerai_token");
    }
  }

  public async restoreSession(): Promise<string | null> {
    return this.tryRefreshToken();
  }

  public async logout(): Promise<void> {
    try {
      await this.post("/auth/logout", {}).catch(() => {});
    } finally {
      this.clearAuth();
    }
  }

  public getCachedUser(): ApiUser | null {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem(USER_CACHE_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  public setCachedUser(user: ApiUser): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(USER_CACHE_KEY, JSON.stringify(user));
  }

  private buildUrl(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined | null>
  ): string {
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = new URL(`${this.baseURL}${cleanEndpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== "") {
          url.searchParams.append(key, String(val));
        }
      });
    }

    return url.toString();
  }

  private onTokenRefreshed(token: string) {
    this.refreshSubscribers.forEach((callback) => callback(token));
    this.refreshSubscribers = [];
  }

  private onTokenRefreshFailed() {
    this.refreshSubscribers.forEach((callback) => callback(""));
    this.refreshSubscribers = [];
  }

  private addRefreshSubscriber(callback: (token: string) => void) {
    this.refreshSubscribers.push(callback);
  }

  private async tryRefreshToken(): Promise<string | null> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      try {
        const response = await fetch(`${this.baseURL}/auth/refresh`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          credentials: "include", // Transports HttpOnly tameerai_refresh_token cookie
        });

        if (!response.ok) {
          this.clearAuth();
          return null;
        }

        const data: AuthTokens = await response.json();
        const token = data.access_token || data.accessToken;
        if (token) {
          this.setToken(token);
          if (data.user) {
            this.setCachedUser(data.user);
          }
          return token;
        }
        this.clearAuth();
        return null;
      } catch {
        this.clearAuth();
        return null;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { params, headers, skipAuthRefresh, ...customConfig } = options;

    let token = this.getToken();
    if (
      !token &&
      !endpoint.includes("/auth/login") &&
      !endpoint.includes("/auth/register") &&
      !endpoint.includes("/auth/refresh") &&
      !endpoint.includes("/material-rates/snapshots") &&
      !endpoint.includes("/material-rates/products") &&
      !endpoint.includes("/material-rates/sources") &&
      typeof window !== "undefined"
    ) {
      token = await this.tryRefreshToken();
    }

    const defaultHeaders: Record<string, string> = {
      Accept: "application/json",
    };

    if (!(customConfig.body instanceof FormData)) {
      defaultHeaders["Content-Type"] = "application/json";
    }

    if (token) {
      defaultHeaders["Authorization"] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...customConfig,
      credentials: "include", // Ensures HttpOnly cookies are carried
      headers: {
        ...defaultHeaders,
        ...headers,
      },
    };

    const url = this.buildUrl(endpoint, params);

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized with Automatic Refresh Token Rotation
      if (
        response.status === 401 &&
        !skipAuthRefresh &&
        !endpoint.includes("/auth/login") &&
        !endpoint.includes("/auth/refresh") &&
        typeof window !== "undefined"
      ) {
        if (!this.isRefreshing) {
          this.isRefreshing = true;
          const newToken = await this.tryRefreshToken();
          this.isRefreshing = false;

          if (newToken) {
            this.onTokenRefreshed(newToken);
            // Retry original request with fresh token
            return this.request<T>(endpoint, {
              ...options,
              skipAuthRefresh: true,
            });
          } else {
            this.onTokenRefreshFailed();
            // Refresh failed; trigger client redirection if on a protected route
            if (window.location.pathname.startsWith("/dashboard")) {
              window.location.href = "/login";
            }
            throw new Error("Session expired. Please log in again.");
          }
        } else {
          // Queue request until ongoing refresh completes
          return new Promise<T>((resolve, reject) => {
            this.addRefreshSubscriber(async (newToken: string) => {
              if (!newToken) {
                reject(new Error("Session expired. Please log in again."));
                return;
              }
              try {
                const retried = await this.request<T>(endpoint, {
                  ...options,
                  skipAuthRefresh: true,
                });
                resolve(retried);
              } catch (err) {
                reject(err);
              }
            });
          });
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message =
          errorData.detail ||
          errorData.message ||
          `Request failed with status ${response.status}`;
        throw new Error(
          typeof message === "string" ? message : JSON.stringify(message)
        );
      }

      return (await response.json()) as T;
    } catch (error) {
      console.warn(`[ApiClient] Request error on ${endpoint}:`, error);
      throw error;
    }
  }

  // HTTP Method Primitives
  public get<T>(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined | null>,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET", params });
  }

  public post<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body:
        body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    });
  }

  public put<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body:
        body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    });
  }

  public patch<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body:
        body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    });
  }

  public delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }

  public upload<T>(
    endpoint: string,
    formData: FormData,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: formData,
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
