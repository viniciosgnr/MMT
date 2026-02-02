
import { createClient } from '@/utils/supabase/client'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

type FetchOptions = RequestInit & {
  headers?: Record<string, string>
}

export async function apiFetch(endpoint: string, options: FetchOptions = {}) {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  const headers: Record<string, string> = {
    ...options.headers,
  }

  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }

  if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  })

  // Handle global errors here if needed (e.g. 401 redirect)
  if (response.status === 401) {
    // Optionally redirect to login or refresh token
    // window.location.href = '/login' (careful with loops)
    console.warn('Unauthorized request')
  }

  return response
}
