export interface User {
  user_id: string;
  username: string;
  role: string;
  organization_id: number;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
}

export interface LoginResponse {
  user: User;
  tokens: Tokens;
  mfa_required?: boolean;
  temp_token?: string;
}

export interface QueryRequest {
  query: string;
  token: string;
}

export interface QueryResponse {
  answer: string;
  sources: Array<{
    doc_id: string;
    chunk_index: number;
  }>;
}

export interface DocumentUpload {
  doc_id: string;
  filename: string;
  status: string;
}

export interface NavItem {
  label: string;
  href: string;
  icon?: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    doc_id: string;
    chunk_index: number;
  }>;
}

export interface AdminInvite {
  id: string;
  email: string;
  role: string;
  created_by: string;
  expires_at: string | null;
  used: boolean;
  used_by: string | null;
  created_at: string | null;
}

export interface AdminDocument {
  doc_id: string;
  filename: string;
  uploaded_by: string;
  uploaded_at: string | null;
  metadata: Record<string, unknown>;
}

export interface AdminUser {
  user_id: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface WebSocketData {
  filename?: string;
  answer?: string;
  sources?: Array<{
    doc_id: string;
    chunk_index: number;
  }>;
}

export interface SearchFilters {
  file_type?: string;
  uploaded_by?: string;
  status?: string;
  tags?: string[];
  date_from?: string;
  date_to?: string;
  file_size_min?: number;
  file_size_max?: number;
  [key: string]: any;
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  size?: number;
}

export interface SearchFacet {
  file_types: string[];
  uploaders: string[];
  statuses: string[];
  tags: string[];
  date_ranges: Array<{
    key: string;
    count: number;
  }>;
}

export interface SearchResult {
  documents: Array<{
    doc_id: string;
    filename: string;
    content: string;
    uploaded_by: string;
    uploaded_at: string;
    file_type: string;
    file_size: number;
    status: string;
    metadata: Record<string, unknown>;
    tags: string[];
    _score?: number;
  }>;
  total: number;
  page: number;
  size: number;
  facets: SearchFacet;
}