// frontend/lib/api/client.ts
// Authentication is handled entirely via HttpOnly cookies set by the backend on login.
// The frontend never touches the token directly — it simply sends credentials: 'include'
// on every request so the browser forwards the cookie automatically.

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const getApiUrl = () => API_BASE

let _refreshPromise: Promise<boolean> | null = null;

/** Ask the backend to refresh the access_token cookie using the refresh_token cookie */
const tryRefreshToken = (): Promise<boolean> => {
  if (_refreshPromise) return _refreshPromise;

  _refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      return res.ok;
    } catch {
      return false;
    } finally {
      _refreshPromise = null;
    }
  })();

  return _refreshPromise;
};

const clearSessionAndRedirect = () => {
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
};

export class ApiClient {
  static async request<T>(
    endpoint: string,
    options: RequestInit = {},
    _isRetry = false
  ): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    let response: Response;
    try {
      response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include', // Always send HttpOnly cookies
      });
    } catch (err: any) {
      const error = new Error('Network error. The server is unreachable.') as any;
      error.code = 'NETWORK_ERROR';
      error.status = 0;
      error.requestId = 'unknown';
      error.isNormalized = true;
      throw error;
    }

    if (response.status === 401 && !_isRetry) {
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        return ApiClient.request<T>(endpoint, options, true);
      }
      clearSessionAndRedirect();
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      let errDetail = 'API Error';
      let errCode = 'SERVER_ERROR';
      let requestId = response.headers.get('x-request-id') || 'unknown';
      
      try {
        const errorData = await response.json();
        errDetail = errorData.detail || errorData.message || errDetail;
        errCode = errorData.code || (response.status === 429 ? 'RATE_LIMITED' : response.status === 403 ? 'FORBIDDEN' : 'SERVER_ERROR');
        requestId = errorData.requestId || requestId;
      } catch {}
      
      const error = new Error(errDetail) as any;
      error.code = errCode;
      error.status = response.status;
      error.requestId = requestId;
      error.isNormalized = true;
      throw error;
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  static get<T>(endpoint: string, options?: RequestInit) {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  static post<T>(endpoint: string, body?: any, options?: RequestInit) {
    const isFormData = body instanceof FormData;
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? (isFormData ? body : JSON.stringify(body)) : undefined,
    });
  }

  static put<T>(endpoint: string, body: any, options?: RequestInit) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  static delete<T>(endpoint: string, options?: RequestInit) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const fetchApi = async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
  const method = (options.method || 'GET').toUpperCase();
  if (method === 'GET') return ApiClient.get<T>(endpoint, options);
  if (method === 'POST') return ApiClient.post<T>(endpoint, options.body, options);
  if (method === 'PUT') return ApiClient.put<T>(endpoint, options.body, options);
  if (method === 'DELETE') return ApiClient.delete<T>(endpoint, options);
  return ApiClient.request<T>(endpoint, options);
};

/** @deprecated No longer reads token — kept only for compatibility */
export const getAuthToken = (): string => '';
