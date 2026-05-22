'use client'

import { useState, useEffect } from 'react'
import ActivityFeed from '@/components/ActivityFeed'

interface DashboardMetrics {
  competitor_count: number
  event_count: number
  activity_score: number
  growth_score: number
  severe_events_count: number
}

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

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [triggerLoading, setTriggerLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      // 1. Fetch Metrics
      const metricsRes = await fetch('http://localhost:8000/api/v1/dashboard/metrics', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (!metricsRes.ok) throw new Error('Failed to load dashboard metrics.')
      const metricsData = await metricsRes.json()
      setMetrics(metricsData)

      // 2. Fetch Events
      const eventsRes = await fetch('http://localhost:8000/api/v1/dashboard/events?limit=10', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (!eventsRes.ok) throw new Error('Failed to load activity feed.')
      const eventsData = await eventsRes.json()
      setEvents(eventsData)
    } catch (err: any) {
      setError(err.message || 'Error occurred while loading console data.')
    } finally {
      setLoading(false)
    }
  }

  const handleTriggerCycle = async () => {
    setTriggerLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch('http://localhost:8000/api/v1/dashboard/trigger', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      })
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Agent execution failed.')
      }

      alert(`Cycle completed! Status: ${data.message} Events Captured: ${data.events_captured}`)
      
      // Refresh dashboard datasets
      await fetchDashboardData()
    } catch (err: any) {
      setError(err.message || 'Error triggering agent cycle.')
    } finally {
      setTriggerLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center gap-4 animate-pulse">
        <div className="w-10 h-10 border-4 border-t-brand-500 border-brand-500/20 rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Aggregating platform intelligence...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Overview Stat Widgets */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Metric 1 */}
        <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-2 relative overflow-hidden group">
          <span className="text-2xl mb-1">🎯</span>
          <span className="text-2xl font-extrabold text-white">{metrics?.competitor_count || 0}</span>
          <span className="text-xs text-gray-400 font-medium">Tracked Competitors</span>
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none group-hover:bg-brand-500/10 transition-all duration-300" />
        </div>

        {/* Metric 2 */}
        <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-2 relative overflow-hidden group">
          <span className="text-2xl mb-1">⚡</span>
          <span className="text-2xl font-extrabold text-white">{metrics?.event_count || 0}</span>
          <span className="text-xs text-gray-400 font-medium">Events Logged</span>
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none group-hover:bg-brand-500/10 transition-all duration-300" />
        </div>

        {/* Metric 3 */}
        <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-2 relative overflow-hidden group">
          <span className="text-2xl mb-1">📈</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white">{metrics?.activity_score || 0}</span>
            <span className="text-xs font-semibold text-brand-400">/ 100</span>
          </div>
          <span className="text-xs text-gray-400 font-medium">Activity Velocity</span>
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none group-hover:bg-brand-500/10 transition-all duration-300" />
        </div>

        {/* Metric 4 */}
        <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-2 relative overflow-hidden group">
          <span className="text-2xl mb-1">🔥</span>
          <span className="text-2xl font-extrabold text-white">{metrics?.severe_events_count || 0}</span>
          <span className="text-xs text-gray-400 font-medium">Critical Updates</span>
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none group-hover:bg-brand-500/10 transition-all duration-300" />
        </div>
      </div>

      {/* Main Console Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Agent Controllers */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-4">
            <h3 className="font-bold text-white text-base">Agent Controller</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Launch the cooperative agent swarm. The scraping agent crawls targets, and the comparison agent registers pricing adjustments, product developments, and hiring changes.
            </p>
            
            <button
              onClick={handleTriggerCycle}
              disabled={triggerLoading}
              className="premium-btn w-full py-3.5 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2 hover:shadow-brand-500/25 transition-all disabled:opacity-50"
            >
              {triggerLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Crawling & Analyzing...</span>
                </>
              ) : (
                <>
                  <span>✨</span>
                  <span>Trigger Agent Swarm</span>
                </>
              )}
            </button>
          </div>

          <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-4">
            <h3 className="font-bold text-white text-base">Competitive Index</h3>
            <div className="flex items-center gap-4 py-2">
              <div className="relative w-20 h-20 shrink-0">
                <svg className="w-full h-full" viewBox="0 0 36 36">
                  <path
                    className="text-white/5"
                    strokeWidth="3.5"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className="text-brand-500"
                    strokeWidth="3.5"
                    strokeDasharray={`${metrics?.growth_score || 0}, 100`}
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-base font-extrabold text-white">{metrics?.growth_score || 0}%</span>
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs font-bold text-white leading-none">Threat Multiplier</span>
                <p className="text-[10px] text-gray-400 leading-normal">
                  Weighted score calculated from active events, updates volume, and severe pricing moves.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Chronological Activity Feed */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-6">
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-white text-base">Intelligence activity Feed</h3>
              <button
                onClick={fetchDashboardData}
                className="text-xs text-brand-400 hover:text-brand-300 font-semibold transition-colors"
              >
                Refresh
              </button>
            </div>
            
            <ActivityFeed events={events} />
          </div>
        </div>
        
      </div>
    </div>
  )
}
