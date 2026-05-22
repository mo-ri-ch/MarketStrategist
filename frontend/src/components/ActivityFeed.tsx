'use client'

interface Event {
  id: number
  competitor_id: number
  competitor_name: string
  event_type: string
  title: string
  description: string
  severity: string
  confidence_score: number
  created_at: string
}

interface ActivityFeedProps {
  events: Event[]
}

export default function ActivityFeed({ events }: ActivityFeedProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-10 bg-white/2 border border-white/5 rounded-2xl">
        <p className="text-sm text-gray-500">No events recorded in this activity cycle.</p>
      </div>
    )
  }

  const getEventTypeEmoji = (type: string) => {
    switch (type.toLowerCase()) {
      case 'pricing':
        return '💰'
      case 'product':
        return '🚀'
      case 'hiring':
        return '👔'
      case 'news':
        return '📰'
      case 'social':
        return '📱'
      default:
        return '🔔'
    }
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-red-500/10 border-red-500/20 text-red-400'
      case 'medium':
        return 'bg-amber-500/10 border-amber-500/20 text-amber-400'
      default:
        return 'bg-blue-500/10 border-blue-500/20 text-blue-400'
    }
  }

  const formatTimestamp = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="flex flex-col gap-4 max-h-[600px] overflow-y-auto pr-2">
      {events.map((event) => (
        <div
          key={event.id}
          className="glass-card p-5 rounded-2xl border border-white/5 flex gap-4 hover:border-brand-500/20 transition-all duration-300 animate-slideUp"
        >
          {/* Visual Icon Badge */}
          <div className="w-12 h-12 rounded-xl bg-brand-500/10 flex items-center justify-center text-lg font-bold shrink-0 border border-brand-500/5">
            {getEventTypeEmoji(event.event_type)}
          </div>

          <div className="flex-grow min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="font-bold text-white text-sm truncate">{event.competitor_name}</span>
              <span className="text-[10px] text-gray-500">•</span>
              <span className="text-xs text-gray-400 font-medium">{formatTimestamp(event.created_at)}</span>
              
              <div className="ml-auto flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded-full border text-[9px] font-bold uppercase tracking-wider ${getSeverityBadge(event.severity)}`}>
                  {event.severity}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/5 text-[9px] font-medium text-gray-400">
                  {Math.round(event.confidence_score * 100)}% Match
                </span>
              </div>
            </div>

            <h5 className="font-semibold text-white text-sm mb-1">{event.title}</h5>
            <p className="text-gray-400 text-xs leading-relaxed">{event.description}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
