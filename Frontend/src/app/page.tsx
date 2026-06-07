'use client'

import { useState, useEffect, useCallback } from 'react'
import DocumentUpload from '@/components/DocumentUpload'
import DocumentList from '@/components/DocumentList'
import ChatWindow from '@/components/ChatWindow'
import { fetchDocuments } from '@/lib/api'
import { Document, UploadResponse } from '@/types'

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loadingDocs, setLoadingDocs] = useState(true)

  const loadDocuments = useCallback(async () => {
    try {
      const docs = await fetchDocuments()
      setDocuments(docs)
    } catch {
      console.error('Failed to load documents')
    } finally {
      setLoadingDocs(false)
    }
  }, [])

  useEffect(() => {
    loadDocuments()
  }, [loadDocuments])

  const handleUploadSuccess = (result: UploadResponse) => {
    console.log('Uploaded:', result)
    loadDocuments()
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shadow-sm">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-lg font-semibold text-gray-900">
            📚 RAG Assistant
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Document-grounded AI
          </p>
        </div>

        <DocumentUpload onUploadSuccess={handleUploadSuccess} />
        <DocumentList documents={documents} loading={loadingDocs} />
      </aside>

      {/* Chat area */}
      <main className="flex-1 flex flex-col">
        <div className="bg-white border-b border-gray-200 px-6 py-3 shadow-sm">
          <h2 className="text-sm font-medium text-gray-700">
            Chat with your documents
          </h2>
          <p className="text-xs text-gray-400">
            Answers are grounded exclusively in uploaded content
          </p>
        </div>

        <div className="flex-1 overflow-hidden">
          <ChatWindow />
        </div>
      </main>
    </div>
  )
}