// frontend/src/lib/api.ts
import { ChatResponse, Document, UploadResponse } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || 'Upload failed')
  }
  return res.json()
}

export async function fetchDocuments(): Promise<Document[]> {
  const res = await fetch(`${API_BASE}/api/documents/`)
  if (!res.ok) throw new Error('Failed to fetch documents')
  return res.json()
}

export async function sendMessage(
  message: string,
  documentIds: string[],          // ← empty array = search all
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      document_ids: documentIds.length > 0 ? documentIds : null,
    }),
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || 'Chat request failed')
  }
  return res.json()
}