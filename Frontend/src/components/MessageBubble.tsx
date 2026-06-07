import { Message } from '@/types'
import CitationBadge from './CitationBadge'

interface Props {
  message: Message
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const isRefusal = message.grounded === false

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : isRefusal
            ? 'bg-amber-50 border border-amber-200 text-amber-900 rounded-bl-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm'
        }`}
      >
        {/* Intent badge for assistant messages */}
        {!isUser && message.intent && (
          <div className="mb-1.5">
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                message.intent === 'summarize'
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              {message.intent === 'summarize' ? 'summarize' : 'retrieve'}
            </span>
          </div>
        )}

        {/* Refusal icon */}
        {isRefusal && (
          <div className="flex items-center gap-1.5 mb-1.5 text-amber-700 text-sm font-medium">
            <span>⚠</span>
            <span>Not found in documents</span>
          </div>
        )}

        {/* Message content */}
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-3 border-t border-gray-100 pt-2">
            <p className="text-xs text-gray-500 mb-1 font-medium">Sources</p>
            {message.citations.map((citation, i) => (
              <CitationBadge key={i} citation={citation} index={i} />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p
          className={`text-xs mt-1.5 ${
            isUser ? 'text-blue-200' : 'text-gray-400'
          }`}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  )
}