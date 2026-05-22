'use client'

import { useState, useEffect } from 'react'

interface Recommendation {
  id: number
  title: string
  strategic_action: string
  rationale: string
  priority: string
  status: string
  created_at: string
}

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null)
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('pending') // pending, implemented, dismissed, all
  const [priorityFilter, setPriorityFilter] = useState<string>('all') // all, high, medium, low

  useEffect(() => {
    fetchRecommendations()
  }, [])

  const fetchRecommendations = async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch('http://localhost:8000/api/v1/recommendations/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to retrieve strategic recommendations.')
      }

      const data = await response.json()
      setRecommendations(data)
    } catch (err: any) {
      setError(err.message || 'Something went wrong while fetching recommendations.')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    setActionLoadingId(id)
    const token = localStorage.getItem('token')

    try {
      const response = await fetch(`http://localhost:8000/api/v1/recommendations/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: newStatus,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to update recommendation status.')
      }

      const updatedRec = await response.json()
      
      // Update state locally
      setRecommendations((prev) =>
        prev.map((rec) => (rec.id === id ? { ...rec, status: updatedRec.status } : rec))
      )
    } catch (err: any) {
      alert(err.message || 'Error updating status.')
    } finally {
      setActionLoadingId(null)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center gap-4 animate-pulse">
        <div className="w-10 h-10 border-4 border-t-brand-500 border-brand-500/20 rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Querying CEO strategist agent...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 rounded-2xl bg-red-950/20 border border-red-500/30 text-center max-w-lg mx-auto mt-10">
        <span className="text-3xl">⚠️</span>
        <h3 className="text-lg font-bold text-white mt-4 mb-2">Workspace Error</h3>
        <p className="text-sm text-gray-400 mb-6">{error}</p>
      </div>
    )
  }

  // Filter logic
  const filteredRecommendations = recommendations.filter((rec) => {
    const matchesStatus = statusFilter === 'all' || rec.status === statusFilter
    const matchesPriority = priorityFilter === 'all' || rec.priority.toLowerCase() === priorityFilter.toLowerCase()
    return matchesStatus && matchesPriority
  })

  // Priority color classes helper
  const getPriorityBadgeClass = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'bg-red-500/10 border-red-500/30 text-red-400'
      case 'medium':
        return 'bg-amber-500/10 border-amber-500/30 text-amber-400'
      default:
        return 'bg-blue-500/10 border-blue-500/30 text-blue-400'
    }
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'implemented':
        return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
      case 'dismissed':
        return 'bg-gray-500/10 border-white/5 text-gray-500'
      default:
        return 'bg-brand-500/10 border-brand-500/30 text-brand-300'
    }
  }

  return (
    <div className="flex flex-col gap-8 animate-fadeIn">
      {/* Header Info Section */}
      <div className="glass-card p-6 rounded-2xl border border-white/5">
        <h2 className="text-xl font-bold text-white">CEO Strategic Intelligence Advisor</h2>
        <p className="text-xs text-gray-400 mt-1 leading-relaxed">
          AI Strategist reasoning loop analyzing competitor website pricing changes, news alerts, and social sentiments to formulate actionable execution recommendations.
        </p>
      </div>

      {/* Control Filters Bar */}
      <div className="flex flex-wrap gap-4 justify-between items-center bg-white/2 border border-white/5 p-4 rounded-2xl">
        {/* Status Tabs */}
        <div className="flex gap-1.5 p-1 bg-dark-400 rounded-xl border border-white/5">
          {['pending', 'implemented', 'dismissed', 'all'].map((tab) => (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                statusFilter === tab
                  ? 'bg-brand-500/15 text-brand-300 border border-brand-500/20'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Priority Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-bold uppercase tracking-wider">Priority:</span>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-dark-400 border border-white/5 rounded-xl px-3 py-2 text-xs font-semibold text-white focus:outline-none focus:border-brand-500"
          >
            <option value="all">ALL PRIORITIES</option>
            <option value="high">HIGH PRIORITY</option>
            <option value="medium">MEDIUM PRIORITY</option>
            <option value="low">LOW PRIORITY</option>
          </select>
        </div>
      </div>

      {/* Feed Cards List */}
      {filteredRecommendations.length === 0 ? (
        <div className="text-center py-20 bg-white/2 border border-dashed border-white/10 rounded-2xl">
          <span className="text-4xl">👔</span>
          <h3 className="text-base font-bold text-white mt-4 mb-1">No Strategic Recommendations Found</h3>
          <p className="text-xs text-gray-500 max-w-xs mx-auto">
            Try adjusting your filters, or execute the cooperative agent swarm to discover competitor movements and trigger recommendations.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {filteredRecommendations.map((rec) => (
            <div
              key={rec.id}
              className={`glass-card p-6 rounded-2xl border flex flex-col gap-6 relative group transition-all duration-300 ${
                rec.status === 'dismissed' ? 'opacity-60 saturate-50 hover:opacity-100 hover:saturate-100' : ''
              }`}
            >
              {/* Badges line */}
              <div className="flex flex-wrap items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded-full border text-[9px] font-extrabold uppercase tracking-widest ${getPriorityBadgeClass(rec.priority)}`}>
                  {rec.priority} Priority
                </span>
                <span className={`px-2.5 py-0.5 rounded-full border text-[9px] font-extrabold uppercase tracking-widest ${getStatusBadgeClass(rec.status)}`}>
                  {rec.status}
                </span>
                
                <span className="ml-auto text-[10px] text-gray-500 font-medium">
                  Formulated: {new Date(rec.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>

              {/* Title & Description */}
              <div className="flex flex-col gap-3">
                <h3 className="font-bold text-white text-base leading-snug">
                  {rec.title}
                </h3>
                
                {/* Rationale explanation block */}
                <p className="text-xs text-gray-400 leading-relaxed font-sans">
                  <span className="font-bold text-gray-300 block mb-1">Market Context & Rationale:</span>
                  {rec.rationale}
                </p>

                {/* Highlighted Strategic Action */}
                <div className="bg-brand-500/5 border border-brand-500/10 p-4 rounded-xl flex flex-col gap-1.5 mt-2">
                  <span className="text-[10px] font-bold text-brand-400 uppercase tracking-wider">
                    Recommended Execution Step:
                  </span>
                  <p className="text-white font-semibold text-xs leading-relaxed">
                    {rec.strategic_action}
                  </p>
                </div>
              </div>

              {/* Actions row */}
              <div className="border-t border-white/5 pt-4 flex justify-end gap-3">
                {rec.status === 'pending' ? (
                  <>
                    <button
                      onClick={() => handleUpdateStatus(rec.id, 'dismissed')}
                      disabled={actionLoadingId === rec.id}
                      className="input-field hover:bg-white/5 px-4 py-2 rounded-lg text-[10px] font-bold text-gray-400 hover:text-white transition-all disabled:opacity-50"
                    >
                      Dismiss Advice
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(rec.id, 'implemented')}
                      disabled={actionLoadingId === rec.id}
                      className="premium-btn px-4 py-2 rounded-lg text-[10px] font-bold text-white transition-all disabled:opacity-50"
                    >
                      {actionLoadingId === rec.id ? 'Updating...' : 'Mark Implemented'}
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleUpdateStatus(rec.id, 'pending')}
                    disabled={actionLoadingId === rec.id}
                    className="input-field hover:bg-brand-500/10 hover:border-brand-500/20 px-4 py-2 rounded-lg text-[10px] font-bold text-gray-400 hover:text-brand-300 transition-all disabled:opacity-50"
                  >
                    {actionLoadingId === rec.id ? 'Reopening...' : 'Reopen Advice'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
