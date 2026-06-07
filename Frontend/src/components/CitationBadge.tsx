import { Citation } from '@/types'

interface Props {
  citation: Citation
  index: number
}

export default function CitationBadge({ citation, index }: Props) {
  return (
    <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800">
      <div className="flex items-center gap-2 font-medium">
        <span className="bg-blue-200 text-blue-900 rounded px-1.5 py-0.5">
          [{index + 1}]
        </span>
        <span>{citation.filename}</span>
        {citation.page_number && (
          <span className="text-blue-600">— page {citation.page_number}</span>
        )}
        {citation.rerank_score !== null && (
          <span className="ml-auto text-blue-500">
            score: {citation.rerank_score.toFixed(2)}
          </span>
        )}
      </div>
      {citation.excerpt && (
        <p className="mt-1 text-blue-700 italic line-clamp-2">
          "{citation.excerpt}"
        </p>
      )}
    </div>
  )
}