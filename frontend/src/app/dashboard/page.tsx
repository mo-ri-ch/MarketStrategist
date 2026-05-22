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
  const [userRole, setUserRole] = useState<string>('viewer')

  // Settings & Reports states
  const [company, setCompany] = useState<any>(null)
  const [webhookUrl, setWebhookUrl] = useState('')
  const [notificationEmail, setNotificationEmail] = useState('')
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [reportDownloading, setReportDownloading] = useState(false)

  useEffect(() => {
    fetchDashboardData()
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      try {
        const u = JSON.parse(storedUser)
        if (u && u.role) {
          setUserRole(u.role)
        }
      } catch (e) {
        console.error(e)
      }
    }
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

      // 3. Fetch Company Details
      const companyRes = await fetch('http://localhost:8000/api/v1/company/my-company', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (companyRes.ok) {
        const companyData = await companyRes.json()
        setCompany(companyData)
        setWebhookUrl(companyData.webhook_url || '')
        setNotificationEmail(companyData.notification_email || '')
      }
    } catch (err: any) {
      setError(err.message || 'Error occurred while loading console data.')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault()
    setSettingsSaving(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch('http://localhost:8000/api/v1/company/my-company', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          webhook_url: webhookUrl || null,
          notification_email: notificationEmail || null
        })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update settings.')
      }

      setCompany(data)
      alert('Notification channels updated successfully!')
    } catch (err: any) {
      setError(err.message || 'Error updating settings.')
    } finally {
      setSettingsSaving(false)
    }
  }

  const handleExportReport = async () => {
    setReportDownloading(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch('http://localhost:8000/api/v1/reports/weekly/trigger', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to generate weekly digest.')
      }

      const blob = await response.blob()
      const contentDisposition = response.headers.get('content-disposition')
      let filename = 'weekly-intelligence-digest.pdf'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1]
        }
      }

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(err.message || 'Error exporting weekly digest.')
    } finally {
      setReportDownloading(false)
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
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

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
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-white text-base">Agent Controller</h3>
              {userRole !== 'admin' && (
                <span className="text-[9px] px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 font-semibold">
                  Locked
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Launch the cooperative agent swarm. The scraping agent crawls targets, and the comparison agent registers pricing adjustments, product developments, and hiring changes.
            </p>
            
            <button
              onClick={handleTriggerCycle}
              disabled={triggerLoading || userRole !== 'admin'}
              className="premium-btn w-full py-3.5 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2 hover:shadow-brand-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              title={userRole !== 'admin' ? 'Insufficient permissions (Admin only)' : 'Trigger agent crawling cycle'}
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

          {/* Settings & Integrations */}
          <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-6">
            <div>
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-white text-base">Settings & Integrations</h3>
                {userRole !== 'admin' && (
                  <span className="text-[9px] px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 font-semibold">
                    Locked
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400 leading-relaxed mt-1">
                Configure automated outbound alerting channels and export executive summaries.
              </p>
            </div>

            <form onSubmit={handleSaveSettings} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-300">Notification Email</label>
                <input
                  type="email"
                  disabled={userRole !== 'admin'}
                  value={notificationEmail}
                  onChange={(e) => setNotificationEmail(e.target.value)}
                  placeholder="alerts@company.com"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand-500/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-300">Webhook URL</label>
                <input
                  type="url"
                  disabled={userRole !== 'admin'}
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  placeholder="https://api.yourdomain.com/webhook"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand-500/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <button
                type="submit"
                disabled={settingsSaving || userRole !== 'admin'}
                className="premium-btn py-2.5 rounded-xl font-semibold text-white text-xs flex items-center justify-center gap-2 hover:shadow-brand-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                title={userRole !== 'admin' ? 'Insufficient permissions (Admin only)' : 'Save changes'}
              >
                {settingsSaving ? (
                  <>
                    <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Update Notification Channels</span>
                )}
              </button>
            </form>

            <hr className="border-white/5" />

            <div className="flex flex-col gap-3">
              <div>
                <h4 className="text-xs font-bold text-white">Weekly Executive Digest</h4>
                <p className="text-[10px] text-gray-400 mt-0.5">
                  Compile and export the latest competitor intelligence, anomaly tracks, and predictions.
                </p>
              </div>

              <button
                onClick={handleExportReport}
                disabled={reportDownloading || (userRole !== 'admin' && userRole !== 'planner')}
                className="w-full py-2.5 rounded-xl border border-brand-500/20 hover:border-brand-500/40 bg-brand-500/5 text-brand-400 hover:text-brand-300 font-semibold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                title={(userRole !== 'admin' && userRole !== 'planner') ? 'Insufficient permissions (Admin/Planner only)' : 'Download digest PDF'}
              >
                {reportDownloading ? (
                  <>
                    <svg className="animate-spin h-3.5 w-3.5 text-brand-400" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Generating Digest...</span>
                  </>
                ) : (
                  <>
                    <span>📄</span>
                    <span>Export Weekly Digest</span>
                  </>
                )}
              </button>
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
