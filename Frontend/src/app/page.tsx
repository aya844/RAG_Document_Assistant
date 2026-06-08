// frontend/src/app/page.tsx
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
  const [selectedIds, setSelectedIds] = useState<string[]>([])

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

  useEffect(() => { loadDocuments() }, [loadDocuments])

  const handleUploadSuccess = (_result: UploadResponse) => { loadDocuments() }

  const handleToggle = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const handleSelectAll = () => setSelectedIds(documents.map(d => d.id))
  const handleClearAll = () => setSelectedIds([])

  // Label for the topbar
  const filterLabel = selectedIds.length === 0
    ? `${documents.length} document${documents.length !== 1 ? 's' : ''} indexed`
    : `${selectedIds.length} of ${documents.length} selected`

  return (
    <div className="flex h-screen" style={{ background: '#faf8f5', fontFamily: 'var(--font-dm-sans)' }}>

      {/* Sidebar */}
      <aside className="w-64 flex flex-col border-r flex-shrink-0"
        style={{ background: '#f5f1eb', borderColor: '#e8e3dc' }}>

        <div className="p-5 border-b" style={{ borderColor: '#e8e3dc' }}>
          <h1 style={{
            fontFamily: 'var(--font-dm-serif)', fontSize: 20,
            color: '#2c2825', letterSpacing: '-.3px', margin: 0,
          }}>
            Folio
          </h1>
          <p style={{ fontSize: 11, color: '#a89f94', marginTop: 2, fontWeight: 300 }}>
            Document intelligence
          </p>
        </div>

        <DocumentUpload onUploadSuccess={handleUploadSuccess} />

        <DocumentList
          documents={documents}
          loading={loadingDocs}
          selectedIds={selectedIds}
          onToggle={handleToggle}
          onSelectAll={handleSelectAll}
          onClearAll={handleClearAll}
        />
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">

        {/* Topbar */}
        <div className="px-6 py-4 border-b flex items-center justify-between"
          style={{ borderColor: '#e8e3dc', background: '#faf8f5' }}>
          <div>
            <h2 style={{
              fontFamily: 'var(--font-dm-serif)', fontSize: 15,
              color: '#2c2825', margin: 0,
            }}>
              Ask your documents
            </h2>
            <p style={{ fontSize: 11, color: '#a89f94', marginTop: 2, fontWeight: 300, margin: 0 }}>
              <span style={{
                display: 'inline-block', width: 5, height: 5, borderRadius: '50%',
                background: selectedIds.length > 0 ? '#c9a96e' : '#8fbc8f',
                marginRight: 5, verticalAlign: 'middle',
              }} />
              {filterLabel}
            </p>
          </div>
          {selectedIds.length > 0 && (
            <button
              onClick={handleClearAll}
              style={{
                fontSize: 11, color: '#8c857c', background: '#ede9e3',
                border: '0.5px solid #ddd8d0', borderRadius: 20,
                padding: '4px 12px', cursor: 'pointer',
              }}
            >
              Clear filter
            </button>
          )}
        </div>

        {/* Chat */}
        <div className="flex-1 overflow-hidden">
          <ChatWindow selectedIds={selectedIds} />
        </div>
      </main>
    </div>
  )
}