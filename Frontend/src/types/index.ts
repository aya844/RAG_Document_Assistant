export interface Document {
  id: string
  filename: string
  file_type: string
  chunk_count: number
  created_at: string
}

export interface Citation {
  filename: string
  page_number: number | null
  rerank_score: number | null
  excerpt: string | null
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  grounded?: boolean
  intent?: string
  timestamp: Date
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  grounded: boolean
  intent: string
}

export interface UploadResponse {
  document_id: string
  filename: string
  pages: number
  parent_chunks: number
  child_chunks: number
}