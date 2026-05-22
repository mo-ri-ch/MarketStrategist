'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface AuditLog {
  id: number
  user_id: number | null
  action: string
  details: Record<string, any> | null
  ip_address: string | null
  created_at: string
}

export default function AuditLogsPage() {
  const router = useRouter()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null)
  
  // Filtering & Pagination State
  const [actionFilter, setActionFilter] = useState('')
  const [userIdFilter, setUserIdFilter] = useState('')
  const [limit, setLimit] = useState(25)
  const [offset, setOffset] = useState(0)
  
  // Selected Log Details Modal State
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      try {
        const u = JSON.parse(storedUser)
        if (u && u.role === 'admin') {
          setIsAdmin(true)
        } else {
          setIsAdmin(false)
          setLoading(false)
        }
      } catch (e) {
        setIsAdmin(false)
        setLoading(false)
      }
    } else {
      setIsAdmin(false)
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isAdmin === true) {
      fetchAuditLogs()
    }
  }, [isAdmin, actionFilter, userIdFilter, offset, limit])

  const fetchAuditLogs = async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) {
      setError('Authentication token not found.')
      setLoading(false)
      return
    }

    try {
      let url = `http://localhost:8000/api/v1/audit/?limit=${limit}&offset=${offset}`
      if (actionFilter.trim()) {
        url += `&action=${encodeURIComponent(actionFilter.trim())}`
      }
      if (userIdFilter.trim()) {
        url += `&user_id=${encodeURIComponent(userIdFilter.trim())}`
      }

      const res = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Access Denied: You do not have permissions to read system audit logs.')
        }
        throw new Error('Failed to retrieve system audit logs.')
      }

      const data = await res.json()
      setLogs(data)
    } catch (err: any) {
      setError(err.message || 'An error occurred while loading audit records.')
    } finally {
      setLoading(false)
    }
  }

  const handleNextPage = () => {
    if (logs.length === limit) {
      setOffset((prev) => prev + limit)
    }
  }

  const handlePrevPage = () => {
    setOffset((prev) => Math.max(0, prev - limit))
  }

  const handleResetFilters = () => {
    setActionFilter('')
    setUserIdFilter('')
    setOffset(0)
  }

  const getActionBadgeClass = (action: string) => {
    const act = action.toLowerCase()
    if (act.includes('create') || act.includes('add')) {
      return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
    }
    if (act.includes('delete') || act.includes('remove')) {
      return 'bg-rose-500/10 border-rose-500/20 text-rose-400'
    }
    if (act.includes('update') || act.includes('change') || act.includes('edit')) {
      return 'bg-amber-500/10 border-amber-500/20 text-amber-400'
    }
    if (act.includes('trigger') || act.includes('swarm') || act.includes('refresh') || act.includes('report')) {
      return 'bg-purple-500/10 border-purple-500/20 text-purple-400'
    }
    return 'bg-blue-500/10 border-blue-500/20 text-blue-400'
  }

  if (isAdmin === false) {
    return (
      <div className="flex flex-col items-center justify-center py-20 animate-fadeIn">
        <div className="w-full max-w-md glass-panel p-8 rounded-3xl border border-red-500/20 shadow-2xl flex flex-col items-center text-center gap-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-red-500/40" />
          <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-3xl shadow-inner">
            🔒
          </div>
          <div>
            <h2 className="text-xl font-bold text-white mb-2">Access Denied</h2>
            <p className="text-xs text-gray-400 leading-relaxed">
              This administrative dashboard displays system action histories and immutable audit trails. Your account role does not have permission to view this page.
            </p>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="premium-btn px-6 py-2.5 rounded-xl font-semibold text-white text-xs w-full hover:shadow-brand-500/25 transition-all"
          >
            Return to Console Overview
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 animate-fadeIn">
      {/* Header and summary cards */}
      <div className="flex justify-between items-center bg-white/2 border border-white/5 p-6 rounded-2xl glass-card">
        <div>
          <h2 className="text-xl font-bold text-white">System Audit Trails</h2>
          <p className="text-xs text-gray-400 mt-1">
            Chronological log of critical administrator actions, configuration updates, and model recalculations.
          </p>
        </div>
        <button
          onClick={fetchAuditLogs}
          className="w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white text-sm transition-all"
          title="Refresh audit trails"
        >
          🔄
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Filters bar */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-white/2 border border-white/5 items-end">
        <div className="flex flex-col gap-1.5 col-span-1">
          <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Action Name</label>
          <input
            type="text"
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value)
              setOffset(0)
            }}
            placeholder="e.g. trigger_swarm"
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-brand-500/40 transition-colors"
          />
        </div>
        
        <div className="flex flex-col gap-1.5 col-span-1">
          <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">User ID</label>
          <input
            type="number"
            value={userIdFilter}
            onChange={(e) => {
              setUserIdFilter(e.target.value)
              setOffset(0)
            }}
            placeholder="e.g. 1"
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-brand-500/40 transition-colors"
          />
        </div>

        <div className="flex flex-col gap-1.5 col-span-1">
          <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Logs Limit</label>
          <select
            value={limit}
            onChange={(e) => {
              setLimit(Number(e.target.value))
              setOffset(0)
            }}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500/40 transition-colors"
          >
            <option value="10" className="bg-dark-500">10 records</option>
            <option value="25" className="bg-dark-500">25 records</option>
            <option value="50" className="bg-dark-500">50 records</option>
            <option value="100" className="bg-dark-500">100 records</option>
          </select>
        </div>

        <button
          onClick={handleResetFilters}
          disabled={!actionFilter && !userIdFilter}
          className="px-4 py-2 border border-white/5 hover:border-white/15 bg-white/2 hover:bg-white/5 text-gray-300 hover:text-white rounded-lg text-xs font-semibold h-[34px] transition-colors disabled:opacity-40"
        >
          Reset Filters
        </button>
      </div>

      {/* Main Table view */}
      <div className="glass-card rounded-2xl border border-white/5 overflow-hidden">
        {loading && logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 animate-pulse">
            <div className="w-8 h-8 border-2 border-t-brand-500 border-brand-500/20 rounded-full animate-spin" />
            <p className="text-xs text-gray-400">Loading audit records...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-20 text-gray-400 italic text-xs">
            No audit log entries matching filters found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-white/1">
                  <th className="p-4 font-bold text-gray-400 uppercase tracking-wider text-[10px]">Log ID</th>
                  <th className="p-4 font-bold text-gray-400 uppercase tracking-wider text-[10px]">Action</th>
                  <th className="p-4 font-bold text-gray-400 uppercase tracking-wider text-[10px]">User ID</th>
                  <th className="p-4 font-bold text-gray-400 uppercase tracking-wider text-[10px]">Client IP</th>
                  <th className="p-4 font-bold text-gray-400 uppercase tracking-wider text-[10px]">Date & Time</th>
                  <th className="p-4 font-bold text-gray-400 uppercase tracking-wider text-[10px] text-right">Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-white/5 hover:bg-white/1 transition-colors">
                    <td className="p-4 font-mono text-gray-400">#{log.id}</td>
                    <td className="p-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold ${getActionBadgeClass(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="p-4 text-white font-medium">
                      {log.user_id ? `User #${log.user_id}` : 'System'}
                    </td>
                    <td className="p-4 text-gray-400 font-mono">
                      {log.ip_address || 'Internal/CLI'}
                    </td>
                    <td className="p-4 text-gray-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="px-2.5 py-1 rounded bg-white/5 border border-white/5 hover:border-white/15 text-white font-semibold text-[10px] transition-all hover:bg-white/10"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination controls */}
      <div className="flex justify-between items-center text-xs">
        <span className="text-gray-400">
          Showing records {offset + 1} - {offset + logs.length}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevPage}
            disabled={offset === 0 || loading}
            className="px-3 py-1.5 rounded border border-white/10 bg-white/5 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
          >
            ◀ Previous
          </button>
          <button
            onClick={handleNextPage}
            disabled={logs.length < limit || loading}
            className="px-3 py-1.5 rounded border border-white/10 bg-white/5 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
          >
            Next ▶
          </button>
        </div>
      </div>

      {/* Details JSON Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-dark-500/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="w-full max-w-lg glass-panel p-6 rounded-3xl border border-white/10 shadow-2xl relative">
            <button
              onClick={() => setSelectedLog(null)}
              className="absolute top-5 right-5 text-gray-400 hover:text-white text-lg transition-colors"
            >
              ✕
            </button>

            <h3 className="text-base font-bold text-white mb-1">
              Inspection: Log #{selectedLog.id}
            </h3>
            <p className="text-[10px] text-gray-400 mb-4 uppercase tracking-wider">
              {selectedLog.action} action details payload
            </p>

            <div className="bg-black/40 border border-white/5 rounded-2xl p-4 overflow-y-auto max-h-[300px] font-mono text-[11px] text-brand-300 leading-relaxed">
              {selectedLog.details ? (
                <pre>{JSON.stringify(selectedLog.details, null, 2)}</pre>
              ) : (
                <span className="italic text-gray-500">No additional details recorded for this action.</span>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-5">
              <button
                onClick={() => setSelectedLog(null)}
                className="input-field hover:bg-white/5 px-4 py-2 rounded-xl font-semibold text-white text-xs"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
