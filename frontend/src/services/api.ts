const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('eduresolve_token');

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // If not FormData, default to application/json
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred.';
    let errorData = null;
    try {
      errorData = await response.json();
      if (errorData.detail) {
        if (typeof errorData.detail === 'string') {
          errorDetail = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorDetail = errorData.detail
            .map((err: any) => {
              const field = Array.isArray(err.loc) ? err.loc.slice(1).join('.') : 'Field';
              return `${field || 'Field'}: ${err.msg}`;
            })
            .join('; ');
        } else {
          errorDetail = JSON.stringify(errorData.detail);
        }
      }
    } catch {
      // response is not JSON
      errorDetail = response.statusText;
    }

    if (response.status === 401) {
      localStorage.removeItem('eduresolve_token');
      localStorage.removeItem('eduresolve_user');
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login?session_expired=1';
      }
    }

    throw new ApiError(response.status, errorDetail, errorData);
  }

  // If download or no content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) => request<T>(endpoint, { ...options, method: 'GET' }),
  post: <T>(endpoint: string, body?: any, options?: RequestInit) => {
    const isFormData = body instanceof FormData;
    return request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: isFormData ? body : JSON.stringify(body),
    });
  },
  put: <T>(endpoint: string, body?: any, options?: RequestInit) => request<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(body),
  }),
  patch: <T>(endpoint: string, body?: any, options?: RequestInit) => request<T>(endpoint, {
    ...options,
    method: 'PATCH',
    body: JSON.stringify(body),
  }),
  delete: <T>(endpoint: string, options?: RequestInit) => request<T>(endpoint, { ...options, method: 'DELETE' }),
  downloadUrl: (endpoint: string) => `${API_BASE}${endpoint}`,
  downloadFile: async (endpoint: string, filename: string) => {
    const token = localStorage.getItem('eduresolve_token');
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'GET',
      headers,
    });
    if (!response.ok) {
      let msg = `Download failed (${response.status})`;
      try {
        const err = await response.json();
        if (err.detail) msg = err.detail;
      } catch {
        // not json
      }
      throw new Error(msg);
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
