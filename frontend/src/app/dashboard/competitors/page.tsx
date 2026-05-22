'use client'

import { useState, useEffect } from 'react'

interface Company {
  id: number
  name: string
  website: string
}

interface Competitor {
  id: number
  company_id: number
  name: string
  website: string
  youtube_url?: string
  instagram_url?: string
  linkedin_url?: string
  facebook_url?: string
  reddit_url?: string
  twitter_url?: string
  medium_url?: string
  threads_url?: string
  status: string
}

export default function CompetitorsPage() {
  const [company, setCompany] = useState<Company | null>(null)
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Add Competitor modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalName, setModalName] = useState('')
  const [modalWebsite, setModalWebsite] = useState('')
  const [modalYoutube, setModalYoutube] = useState('')
  const [modalLinkedin, setModalLinkedin] = useState('')
  const [modalTwitter, setModalTwitter] = useState('')
  const [modalReddit, setModalReddit] = useState('')
  const [modalLoading, setModalLoading] = useState(false)
  const [modalError, setModalError] = useState('')

  useEffect(() => {
    fetchCompanyAndCompetitors()
  }, [])

  const fetchCompanyAndCompetitors = async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      // 1. Get user's onboarded company
      const companyRes = await fetch('http://localhost:8000/api/v1/company/my-company', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!companyRes.ok) {
        if (companyRes.status === 404) {
          throw new Error('No company onboarded. Please onboard your company profile first.')
        }
        throw new Error('Failed to load company profile.')
      }
      
      const companyData = await companyRes.json()
      setCompany(companyData)

      // 2. Get competitors for this company
      const competitorsRes = await fetch(`http://localhost:8000/api/v1/competitor/?company_id=${companyData.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (competitorsRes.ok) {
        const competitorsData = await competitorsRes.json()
        setCompetitors(competitorsData)
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong while fetching data.')
    } finally {
      setLoading(false)
    }
  }

  const handleAddCompetitor = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!company) return
    setModalError('')
    setModalLoading(true)
    const token = localStorage.getItem('token')

    try {
      const response = await fetch('http://localhost:8000/api/v1/competitor/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          company_id: company.id,
          name: modalName,
          website: modalWebsite,
          youtube_url: modalYoutube || null,
          linkedin_url: modalLinkedin || null,
          twitter_url: modalTwitter || null,
          reddit_url: modalReddit || null,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to add competitor.')
      }

      setCompetitors((prev) => [...prev, data])
      setIsModalOpen(false)
      // Reset form
      setModalName('')
      setModalWebsite('')
      setModalYoutube('')
      setModalLinkedin('')
      setModalTwitter('')
      setModalReddit('')
    } catch (err: any) {
      setModalError(err.message || 'Something went wrong.')
    } finally {
      setModalLoading(false)
    }
  }

  const handleDeleteCompetitor = async (id: number) => {
    if (!confirm('Are you sure you want to stop tracking this competitor? All scraped histories will be archived.')) return
    const token = localStorage.getItem('token')

    try {
      const response = await fetch(`http://localhost:8000/api/v1/competitor/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to delete competitor.')
      }

      setCompetitors((prev) => prev.filter((item) => item.id !== id))
    } catch (err: any) {
      alert(err.message || 'Error deleting competitor.')
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center gap-4 animate-pulse">
        <div className="w-10 h-10 border-4 border-t-brand-500 border-brand-500/20 rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Fetching tracked targets...</p>
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

  return (
    <div className="flex flex-col gap-8 animate-fadeIn">
      {/* Header section with Add Competitor CTA */}
      <div className="flex justify-between items-center bg-white/2 border border-white/5 p-6 rounded-2xl glass-card">
        <div>
          <h2 className="text-xl font-bold text-white">Tracking Landscape for {company?.name}</h2>
          <p className="text-xs text-gray-400 mt-1">
            Specify the company URLs and social handles you want the scraper and monitoring agents to track.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="premium-btn px-5 py-3 rounded-xl font-semibold text-white text-sm flex items-center gap-2"
        >
          <span>➕</span>
          <span>Add Competitor</span>
        </button>
      </div>

      {competitors.length === 0 ? (
        <div className="text-center py-20 bg-white/2 border border-dashed border-white/10 rounded-2xl">
          <span className="text-4xl">🔍</span>
          <h3 className="text-lg font-bold text-white mt-4 mb-1">No Competitors Registered</h3>
          <p className="text-sm text-gray-400 max-w-sm mx-auto mb-6">
            Add your primary competitors to begin mapping strategic updates, news spikes, and social analytics.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="premium-btn px-5 py-2.5 rounded-xl font-semibold text-white text-xs"
          >
            Add First Target
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {competitors.map((comp) => (
            <div key={comp.id} className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col justify-between gap-6 relative group">
              <button
                onClick={() => handleDeleteCompetitor(comp.id)}
                className="absolute top-4 right-4 text-gray-500 hover:text-red-400 text-sm opacity-0 group-hover:opacity-100 transition-opacity"
                title="Remove Competitor"
              >
                🗑️
              </button>

              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center font-bold text-brand-400 text-sm">
                    {comp.name.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h4 className="font-bold text-white text-base leading-tight">{comp.name}</h4>
                    <a
                      href={comp.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-brand-400 hover:text-brand-300 transition-colors truncate block max-w-[200px]"
                    >
                      {comp.website.replace(/^https?:\/\//, '')}
                    </a>
                  </div>
                </div>
              </div>

              <CompetitorPredictionPanel competitorId={comp.id} />

              {/* Connected channels summary */}
              <div className="border-t border-white/5 pt-4 flex items-center justify-between">
                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Scraping Channels:</span>
                <div className="flex gap-2.5 text-sm">
                  <span
                    className={`cursor-default ${comp.linkedin_url ? 'text-blue-400 opacity-100' : 'text-gray-600 opacity-30'}`}
                    title={comp.linkedin_url ? `LinkedIn: ${comp.linkedin_url}` : 'No LinkedIn linked'}
                  >
                    🔗
                  </span>
                  <span
                    className={`cursor-default ${comp.twitter_url ? 'text-sky-400 opacity-100' : 'text-gray-600 opacity-30'}`}
                    title={comp.twitter_url ? `X/Twitter: ${comp.twitter_url}` : 'No X/Twitter linked'}
                  >
                    🐦
                  </span>
                  <span
                    className={`cursor-default ${comp.youtube_url ? 'text-red-500 opacity-100' : 'text-gray-600 opacity-30'}`}
                    title={comp.youtube_url ? `YouTube: ${comp.youtube_url}` : 'No YouTube linked'}
                  >
                    📺
                  </span>
                  <span
                    className={`cursor-default ${comp.reddit_url ? 'text-orange-500 opacity-100' : 'text-gray-600 opacity-30'}`}
                    title={comp.reddit_url ? `Reddit: ${comp.reddit_url}` : 'No Reddit linked'}
                  >
                    👽
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Competitor Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-dark-500/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fadeIn">
          <div className="w-full max-w-lg glass-panel p-8 rounded-3xl border border-white/10 shadow-2xl relative">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-5 right-5 text-gray-400 hover:text-white text-lg transition-colors"
            >
              ✕
            </button>

            <h3 className="text-xl font-bold text-white mb-1">Add Competitor Target</h3>
            <p className="text-xs text-gray-400 mb-6">Configure details for Scraper & Social Sentiment Agents.</p>

            {modalError && (
              <div className="mb-4 p-3 rounded-lg bg-red-950/40 border border-red-500/30 text-red-200 text-xs flex items-center gap-2">
                <span>⚠️</span>
                <p>{modalError}</p>
              </div>
            )}

            <form onSubmit={handleAddCompetitor} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Competitor Name</label>
                <input
                  type="text"
                  required
                  placeholder="Competitor Inc."
                  value={modalName}
                  onChange={(e) => setModalName(e.target.value)}
                  className="input-field w-full px-4 py-2.5 rounded-xl text-white placeholder-gray-600 text-sm focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Website URL</label>
                <input
                  type="url"
                  required
                  placeholder="https://competitor.com"
                  value={modalWebsite}
                  onChange={(e) => setModalWebsite(e.target.value)}
                  className="input-field w-full px-4 py-2.5 rounded-xl text-white placeholder-gray-600 text-sm focus:outline-none"
                />
              </div>

              <div className="border-t border-white/5 my-2 pt-3">
                <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider block mb-3">
                  Social Channels (Optional)
                </span>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] text-gray-400 uppercase tracking-wider">LinkedIn URL</label>
                    <input
                      type="url"
                      placeholder="https://linkedin.com/company/..."
                      value={modalLinkedin}
                      onChange={(e) => setModalLinkedin(e.target.value)}
                      className="input-field w-full px-3 py-2 rounded-lg text-white placeholder-gray-600 text-xs focus:outline-none"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] text-gray-400 uppercase tracking-wider">X/Twitter URL</label>
                    <input
                      type="url"
                      placeholder="https://twitter.com/..."
                      value={modalTwitter}
                      onChange={(e) => setModalTwitter(e.target.value)}
                      className="input-field w-full px-3 py-2 rounded-lg text-white placeholder-gray-600 text-xs focus:outline-none"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] text-gray-400 uppercase tracking-wider">YouTube URL</label>
                    <input
                      type="url"
                      placeholder="https://youtube.com/..."
                      value={modalYoutube}
                      onChange={(e) => setModalYoutube(e.target.value)}
                      className="input-field w-full px-3 py-2 rounded-lg text-white placeholder-gray-600 text-xs focus:outline-none"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] text-gray-400 uppercase tracking-wider">Reddit Subreddit URL</label>
                    <input
                      type="url"
                      placeholder="https://reddit.com/r/..."
                      value={modalReddit}
                      onChange={(e) => setModalReddit(e.target.value)}
                      className="input-field w-full px-3 py-2 rounded-lg text-white placeholder-gray-600 text-xs focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="input-field hover:bg-white/5 px-5 py-2.5 rounded-xl font-semibold text-white text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="premium-btn px-6 py-2.5 rounded-xl font-semibold text-white text-xs disabled:opacity-50"
                >
                  {modalLoading ? 'Configuring Agents...' : 'Register Competitor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

interface Prediction {
  predicted_action: string
  description: string
  confidence_score: number
  trigger_events?: Array<{
    id: number
    title: string
    event_type: string
  }>
  updated_at: string
}

function CompetitorPredictionPanel({ competitorId }: { competitorId: number }) {
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  const fetchPrediction = async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    try {
      const response = await fetch(`http://localhost:8000/api/v1/predictor/${competitorId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      if (!response.ok) {
        throw new Error('Failed to load predictions.')
      }
      const data = await response.json()
      setPrediction(data)
    } catch (err: any) {
      setError(err.message || 'Error loading prediction.')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    try {
      const response = await fetch(`http://localhost:8000/api/v1/predictor/${competitorId}/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      if (!response.ok) {
        throw new Error('Failed to refresh prediction.')
      }
      const data = await response.json()
      setPrediction(data)
    } catch (err: any) {
      setError(err.message || 'Error refreshing prediction.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen && !prediction) {
      fetchPrediction()
    }
  }, [isOpen])

  return (
    <div className="mt-2 border-t border-white/5 pt-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-left text-xs font-semibold text-brand-400 hover:text-brand-300 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          🔮 Predictive Intelligence
        </span>
        <span>{isOpen ? '▲ Hide' : '▼ Expand'}</span>
      </button>

      {isOpen && (
        <div className="mt-2.5 p-3.5 rounded-xl bg-white/3 border border-white/5 flex flex-col gap-2.5 text-xs text-gray-300">
          {loading && !prediction ? (
            <div className="flex items-center gap-2 text-gray-400 py-1.5">
              <div className="w-3.5 h-3.5 border-2 border-t-brand-400 border-brand-400/20 rounded-full animate-spin" />
              <span>Analyzing competitor actions...</span>
            </div>
          ) : error ? (
            <p className="text-red-400">{error}</p>
          ) : prediction ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Forecasted Next Move</span>
                  <span className="text-white font-bold text-sm">{prediction.predicted_action}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Confidence</span>
                  <span className="text-brand-400 font-bold text-sm">{(prediction.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-brand-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${prediction.confidence_score * 100}%` }}
                />
              </div>

              <div>
                <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-0.5">Rationale</span>
                <p className="text-gray-300 leading-relaxed text-[11px]">{prediction.description}</p>
              </div>

              {prediction.trigger_events && prediction.trigger_events.length > 0 && (
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Causal Events</span>
                  <div className="flex flex-col gap-1.5">
                    {prediction.trigger_events.map((evt) => (
                      <div key={evt.id} className="p-2 rounded bg-white/5 border border-white/5 flex items-start gap-1.5">
                        <span className="text-brand-400 mt-0.5">▪</span>
                        <div>
                          <p className="text-white font-semibold text-[10.5px] leading-tight">{evt.title}</p>
                          <p className="text-[9px] text-gray-500 uppercase">{evt.event_type}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-between items-center border-t border-white/5 pt-2 mt-1">
                <span className="text-[9px] text-gray-500">
                  Updated: {new Date(prediction.updated_at).toLocaleDateString()}
                </span>
                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-white font-semibold text-[9px] transition-all flex items-center gap-1"
                >
                  {loading ? 'Refreshing...' : '🔄 Recalculate'}
                </button>
              </div>
            </>
          ) : (
            <p className="text-gray-400 italic">No predictions generated yet.</p>
          )}
        </div>
      )}
    </div>
  )
}
