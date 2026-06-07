'use client'

import { useState, useRef } from 'react'
import { uploadDocument } from '@/lib/api'
import { UploadResponse } from '@/types'

interface Props {
  onUploadSuccess: (result: UploadResponse) => void
}

export default function DocumentUpload({ onUploadSuccess }: Props) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['pdf', 'txt'].includes(ext || '')) {
      setError('Only PDF and TXT files are supported')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const result = await uploadDocument(file)
      onUploadSuccess(result)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="p-4 border-b border-gray-200">
      <h2 className="text-sm font-semibold text-gray-700 mb-3">
        Upload Document
      </h2>

      <div
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-blue-600">Processing document...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div className="text-3xl">📄</div>
            <p className="text-sm text-gray-600">
              Drop a file or <span className="text-blue-600 font-medium">browse</span>
            </p>
            <p className="text-xs text-gray-400">PDF, TXT</p>
          </div>
        )}
      </div>

      {error && (
        <p className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded-lg">
          {error}
        </p>
      )}
    </div>
  )
}