
import { createClient } from '@/utils/supabase/client'

export const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

type FetchOptions = RequestInit & {
  headers?: Record<string, string>
  params?: Record<string, string | number | boolean>
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

  let url = `${API_URL}${endpoint}`
  if (options.params) {
    const searchParams = new URLSearchParams()
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString
    }
  }

  const response = await fetch(url, {
    cache: 'no-store',
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

// M2 - Metrological Confirmation APIs
export async function planCalibration(taskId: number, data: any) {
  return apiFetch(`/calibration/tasks/${taskId}/plan`, {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

export async function executeCalibration(taskId: number, data: any) {
  return apiFetch(`/calibration/tasks/${taskId}/execute`, {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

export async function uploadCertificate(taskId: number, data: any) {
  return apiFetch(`/calibration/tasks/${taskId}/certificate`, {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

export async function validateCertificate(taskId: number) {
  const res = await apiFetch(`/calibration/tasks/${taskId}/certificate/validate`, {
    method: 'POST'
  })
  return res.json()
}

export async function getTagSealHistory(tagId: number) {
  const res = await apiFetch(`/calibration/tags/${tagId}/seals`)
  return res.json()
}

export async function failCalibrationTask(taskId: number, reason: string) {
  const res = await apiFetch(`/calibration/tasks/${taskId}/fail`, {
    method: 'POST',
    params: { reason } // using query param as seen in router
  })
  return res.json()
}
