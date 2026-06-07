'use client'

import { Document } from '@/types'

interface Props {
  documents: Document[]
  loading: boolean
}

export default function DocumentList({ documents, loading }: Props) {
  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-gray-400">
        No documents yet. Upload one to start chatting.
      </div>
    )
  }

  return (
    <div className="p-4 flex-1 overflow-y-auto">
      <h2 className="text-sm font-semibold text-gray-700 mb-3">
        Documents ({documents.length})
      </h2>
      <div className="space-y-2">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="p-3 bg-gray-50 rounded-xl border border-gray-200 hover:border-blue-300 transition-colors"
          >
            <div className="flex items-start gap-2">
              <span className="text-lg">
                {doc.file_type === 'pdf' ? '📕' : '📄'}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {doc.filename}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {new Date(doc.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}