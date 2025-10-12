import axios from 'axios';
import { LoginResponse, QueryRequest, QueryResponse, DocumentUpload, SearchRequest, SearchResult, SearchFacet } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          // Retry the original request
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return axios(error.config);
        } catch (refreshError) {
          // Refresh failed, logout
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (inviteToken: string, email: string, password: string) => {
    const response = await api.post('/auth/register', {
      invite_token: inviteToken,
      email,
      password,
    });
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

export const ragAPI = {
  query: async (query: string): Promise<QueryResponse> => {
    const response = await api.post('/qa/ask', { query });
    return response.data;
  },
};

export const documentAPI = {
  upload: async (file: File): Promise<DocumentUpload> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/policies/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const adminAPI = {
  // Invite management
  createInvite: async (email: string, role: string) => {
    const response = await api.post('/admin/invite', { email, role });
    return response.data;
  },

  listInvites: async () => {
    const response = await api.get('/admin/invites');
    return response.data;
  },

  revokeInvite: async (inviteId: string) => {
    const response = await api.post(`/admin/revoke-invite/${inviteId}`);
    return response.data;
  },

  // Document management
  getPendingDocuments: async () => {
    const response = await api.get('/admin/documents/pending');
    return response.data;
  },

  approveDocument: async (docId: string, action: 'approve' | 'reject') => {
    const response = await api.post('/admin/documents/approve', { doc_id: docId, action });
    return response.data;
  },

  // User management
  getUsers: async () => {
    const response = await api.get('/admin/users');
    return response.data;
  },

  // Security audit
  getSecurityAuditSummary: async () => {
    const response = await api.get('/admin/security-audit/summary');
    return response.data;
  },

  runSecurityAudit: async () => {
    const response = await api.get('/admin/security-audit');
    return response.data;
  },
};

export const searchAPI = {
  searchDocuments: async (searchRequest: SearchRequest): Promise<SearchResult> => {
    const response = await api.post('/search/documents', searchRequest);
    return response.data;
  },

  getFacets: async (): Promise<SearchFacet> => {
    const response = await api.get('/search/facets');
    return response.data;
  },
};

export const analyticsAPI = {
  getUserActivity: async (days: number = 30) => {
    const response = await api.get(`/analytics/user-activity?days=${days}`);
    return response.data;
  },

  getSystemMetrics: async (hours: number = 24) => {
    const response = await api.get(`/analytics/system-metrics?hours=${hours}`);
    return response.data;
  },

  trackEvent: async (eventType: string, eventData?: any) => {
    const response = await api.post('/analytics/track', {
      event_type: eventType,
      event_data: eventData,
    });
    return response.data;
  },
};

export default api;