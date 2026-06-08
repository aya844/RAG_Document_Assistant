// frontend/src/components/DocumentList.tsx
'use client'
import { Document } from '@/types'

interface Props {
  documents: Document[]
  loading: boolean
  selectedIds: string[]
  onToggle: (id: string) => void
  onSelectAll: () => void
  onClearAll: () => void
}

export default function DocumentList({
  documents, loading, selectedIds, onToggle, onSelectAll, onClearAll,
}: Props) {

  if (loading) {
    return (
      <div className="p-4 space-y-2">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-11 rounded-lg animate-pulse"
            style={{ background: '#ede9e3' }} />
        ))}
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="p-5 text-center" style={{ fontSize: 12, color: '#b5aea6' }}>
        No documents yet. Upload one to begin.
      </div>
    )
  }

  const allSelected = selectedIds.length === documents.length
  const noneSelected = selectedIds.length === 0

  return (
    <div className="flex-1 overflow-y-auto flex flex-col min-h-0">

      {/* Header row */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px 6px',
      }}>
        <span style={{ fontSize: 10, fontWeight: 500, color: '#b5aea6',
          letterSpacing: '.07em', textTransform: 'uppercase' }}>
          Library ({documents.length})
        </span>
        <button
          onClick={allSelected ? onClearAll : onSelectAll}
          style={{
            fontSize: 10, color: '#8c857c', background: 'none',
            border: 'none', cursor: 'pointer', padding: '2px 6px',
            borderRadius: 4,
          }}
        >
          {allSelected ? 'Deselect all' : 'Select all'}
        </button>
      </div>

      {/* Hint */}
      <div style={{ padding: '0 14px 8px' }}>
        <p style={{ fontSize: 10, color: '#b5aea6', fontStyle: 'italic' }}>
          {noneSelected
            ? 'No filter — searching all documents'
            : `Searching ${selectedIds.length} of ${documents.length} document${selectedIds.length > 1 ? 's' : ''}`}
        </p>
      </div>

      {/* Document rows */}
      <div style={{ padding: '0 8px 8px' }}>
        {documents.map(doc => {
          const checked = selectedIds.includes(doc.id)
          return (
            <label
              key={doc.id}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 10px', borderRadius: 8, marginBottom: 2,
                cursor: 'pointer',
                background: checked ? '#e8e2d9' : 'transparent',
                border: checked ? '0.5px solid #ddd8d0' : '0.5px solid transparent',
                transition: 'background .12s',
              }}
            >
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggle(doc.id)}
                style={{
                  width: 14, height: 14, accentColor: '#5c5349',
                  flexShrink: 0, cursor: 'pointer',
                }}
              />

              {/* File icon */}
              <div style={{
                width: 26, height: 26, borderRadius: 6, flexShrink: 0,
                background: checked ? '#ddd8d0' : '#ede9e3',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, color: checked ? '#5c5349' : '#8c857c',
              }}>
                {doc.file_type === 'pdf' ? 'PDF' : 'TXT'}
              </div>

              {/* Info */}
              <div style={{ minWidth: 0, flex: 1 }}>
                <p style={{
                  fontSize: 12, fontWeight: 500, margin: 0,
                  color: checked ? '#3d3530' : '#5c5349',
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                }}>
                  {doc.filename}
                </p>
                <p style={{ fontSize: 10, color: '#b5aea6', margin: 0 }}>
                  {new Date(doc.created_at).toLocaleDateString()}
                </p>
              </div>
            </label>
          )
        })}
      </div>
    </div>
  )
}