import axios from 'axios'

const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000' })

export const auth = {
  login: (data: { email: string; password: string }) => api.post('/auth/login', data).then(r=>r.data),
  register: (data: { invite_token: string; email: string; password: string }) => api.post('/auth/register', data).then(r=>r.data)
}

export const search = {
  documents: (data:any) => api.post('/search/documents', data).then(r=>r.data),
  ask: (data:any) => api.post('/search/ask', data).then(r=>r.data)
}

export default api
