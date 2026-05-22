'use client'

import { useState, useEffect } from 'react'

interface Competitor {
  id: number
  name: string
  website: string
}

interface CompetitorEvent {
  id: number
  event_type: string
  title: string
  description: string
  severity: string
  confidence_score: number
  created_at: string
}

interface Alert {
  id: number
  competitor_id: number
  event_id: number
  is_read: boolean
  created_at: string
  competitor: Competitor
  event: CompetitorEvent
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filterUnread, setFilterUnread] = useState(false)
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  useEffect(() => {
    fetchAlerts()
  }, [filterUnread])

  const fetchAlerts = async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const url = filterUnread 
        ? 'http://localhost:8000/api/v1/alerts/?is_read=false'
        : 'http://localhost:8000/api/v1/alerts/'

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to load alerts list.')
      }

      const data = await response.json()
      setAlerts(data)
    } catch (err: any) {
      setError(err.message || 'Error occurred while loading alerts.')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleRead = async (alertId: number, currentReadStatus: boolean) => {
    setActionLoading(alertId)
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`http://localhost:8000/api/v1/alerts/${alertId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ is_read: !currentReadStatus }),
      })

      if (!response.ok) {
        throw new Error('Failed to update alert status.')
      }

      const updatedAlert = await response.json()
      setAlerts((prev) =>
        prev.map((alert) => (alert.id === alertId ? updatedAlert : alert))
      )
    } catch (err: any) {
      alert(err.message || 'Error updating alert.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleMarkAllRead = async () => {
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch('http://localhost:8000/api/v1/alerts/read-all', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to mark all alerts as read.')
      }

      // Refresh alerts from backend
      await fetchAlerts()
    } catch (err: any) {
      alert(err.message || 'Error marking alerts as read.')
    }
  }

  const handleDeleteAlert = async (alertId: number) => {
    if (!confirm('Are you sure you want to dismiss this alert?')) return
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`http://localhost:8000/api/v1/alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to delete alert.')
      }

      setAlerts((prev) => prev.filter((alert) => alert.id !== alertId))
    } catch (err: any) {
      alert(err.message || 'Error deleting alert.')
    }
  }

  const getEventTypeEmoji = (type: string) => {
    switch (type?.toLowerCase()) {
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
    switch (severity?.toLowerCase()) {
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

  if (loading && alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center gap-4 animate-pulse">
        <div className="w-10 h-10 border-4 border-t-brand-500 border-brand-500/20 rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Loading strategic notifications...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8 animate-fadeIn">
      {/* Top Banner Control Panel */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white/2 border border-white/5 p-6 rounded-2xl glass-card">
        <div>
          <h2 className="text-xl font-bold text-white">Strategic Platform Alerts</h2>
          <p className="text-xs text-gray-400 mt-1">
            Crucial product updates, pricing models adjustment, and corporate shift notifications.
          </p>
        </div>
        
        <div className="flex items-center gap-3.5">
          {/* Toggle unread filter */}
          <button
            onClick={() => setFilterUnread(!filterUnread)}
            className={`px-4 py-2.5 rounded-xl border text-xs font-bold transition-all duration-300 ${
              filterUnread
                ? 'bg-brand-500/10 border-brand-500/30 text-brand-300'
                : 'bg-white/2 border-white/5 text-gray-400 hover:text-white'
            }`}
          >
            {filterUnread ? 'Showing Unread Only' : 'Filter by Unread'}
          </button>

          {/* Mark all as read */}
          <button
            onClick={handleMarkAllRead}
            disabled={alerts.filter(a => !a.is_read).length === 0}
            className="input-field hover:bg-white/5 px-4 py-2.5 rounded-xl font-bold text-white text-xs disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            ✓ Mark All Read
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30 text-center max-w-lg mx-auto text-sm text-red-400">
          ⚠️ {error}
        </div>
      )}

      {/* Main Alerts Feed */}
      {alerts.length === 0 ? (
        <div className="text-center py-20 bg-white/2 border border-dashed border-white/10 rounded-2xl">
          <span className="text-4xl">🔔</span>
          <h3 className="text-lg font-bold text-white mt-4 mb-1">No Alerts Received</h3>
          <p className="text-sm text-gray-400 max-w-xs mx-auto">
            {filterUnread 
              ? 'Great work! You have read all outstanding notifications.' 
              : 'Add competitors and run crawling agent swarm cycles to capture competitor events.'}
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`glass-card p-6 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-6 transition-all duration-300 ${
                alert.is_read 
                  ? 'border-white/5 opacity-60 hover:opacity-90' 
                  : 'border-brand-500/20 shadow-[0_0_15px_-3px_rgba(var(--color-brand-500),0.1)] hover:border-brand-500/45'
              }`}
            >
              {/* Alert Meta and content */}
              <div className="flex gap-4 items-start min-w-0 flex-grow">
                {/* Event Type Icon */}
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold shrink-0 border transition-all ${
                  alert.is_read 
                    ? 'bg-white/2 border-white/5' 
                    : 'bg-brand-500/10 border-brand-500/15 text-brand-300'
                }`}>
                  {getEventTypeEmoji(alert.event?.event_type)}
                </div>

                <div className="flex-grow min-w-0">
                  <div className="flex flex-wrap items-center gap-2.5 mb-1.5">
                    <span className="font-extrabold text-white text-sm truncate">
                      {alert.competitor?.name}
                    </span>
                    <span className="text-[10px] text-gray-600">•</span>
                    <span className="text-xs text-gray-400 font-medium">
                      {formatTimestamp(alert.created_at)}
                    </span>
                    
                    {!alert.is_read && (
                      <span className="px-1.5 py-0.5 rounded bg-brand-500 text-[8px] font-black text-dark-500 uppercase tracking-widest leading-none">
                        New
                      </span>
                    )}

                    <div className="flex items-center gap-2 md:ml-2">
                      <span className={`px-2 py-0.5 rounded-full border text-[9px] font-bold uppercase tracking-wider ${getSeverityBadge(alert.event?.severity)}`}>
                        {alert.event?.severity}
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/5 text-[9px] font-medium text-gray-400">
                        {Math.round((alert.event?.confidence_score || 1.0) * 100)}% Match
                      </span>
                    </div>
                  </div>

                  <h4 className="font-bold text-white text-base mb-1">{alert.event?.title}</h4>
                  <p className="text-gray-400 text-xs leading-relaxed max-w-4xl">
                    {alert.event?.description}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3.5 shrink-0 ml-auto md:ml-0">
                <button
                  onClick={() => handleToggleRead(alert.id, alert.is_read)}
                  disabled={actionLoading === alert.id}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all border ${
                    alert.is_read
                      ? 'border-white/5 bg-white/2 text-gray-400 hover:text-white hover:bg-white/5'
                      : 'border-brand-500/20 bg-brand-500/5 text-brand-300 hover:bg-brand-500/10'
                  }`}
                  title={alert.is_read ? 'Mark as Unread' : 'Mark as Read'}
                >
                  {actionLoading === alert.id 
                    ? '...' 
                    : alert.is_read 
                      ? '🕳️ Mark Unread' 
                      : '✓ Mark Read'}
                </button>
                <button
                  onClick={() => handleDeleteAlert(alert.id)}
                  className="p-2 rounded-xl hover:bg-red-950/20 border border-transparent hover:border-red-500/20 text-gray-500 hover:text-red-400 transition-all"
                  title="Dismiss Alert"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
