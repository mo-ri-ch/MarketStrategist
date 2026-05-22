'use client'

import { useState, useEffect } from 'react'

interface Company {
  id: number
  name: string
  website: string
}

interface Competitor {
  id: number
  name: string
  website: string
  status: string
}

interface Insight {
  id: number
  insight_type: string
  title: string
  description: string
  sentiment_score: number
  competitor_id?: number
  data_points: any
  created_at: string
}

export default function MarketIntelligencePage() {
  const [company, setCompany] = useState<Company | null>(null)
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [insights, setInsights] = useState<Insight[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [trackLoadingId, setTrackLoadingId] = useState<number | null>(null)
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    fetchMarketData()
  }, [])

  const fetchMarketData = async () => {
    setLoading(true)
    setError('')
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      // 1. Fetch Company
      const companyRes = await fetch('http://localhost:8000/api/v1/company/my-company', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (!companyRes.ok) {
        if (companyRes.status === 404) {
          throw new Error('Please onboard your company profile first.')
        }
        throw new Error('Failed to load company profile.')
      }
      const companyData = await companyRes.json()
      setCompany(companyData)

      // 2. Fetch Competitors
      const competitorsRes = await fetch(`http://localhost:8000/api/v1/competitor/?company_id=${companyData.id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (competitorsRes.ok) {
        const competitorsData = await competitorsRes.json()
        setCompetitors(competitorsData)
      }

      // 3. Fetch Insights
      const insightsRes = await fetch('http://localhost:8000/api/v1/insights/', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (insightsRes.ok) {
        const insightsData = await insightsRes.json()
        setInsights(insightsData)
      }
    } catch (err: any) {
      setError(err.message || 'Error loading market intelligence datasets.')
    } finally {
      setLoading(false)
    }
  }

  const handleTrackCompetitor = async (insightId: number, name: string, website: string) => {
    if (!company) return
    setTrackLoadingId(insightId)
    setSuccessMessage('')
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
          name: name,
          website: website,
        }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to track competitor.')
      }

      setSuccessMessage(`Successfully added "${name}" to tracked competitors list!`)
      // Refresh datasets
      await fetchMarketData()
    } catch (err: any) {
      alert(err.message || 'Error tracking discovered competitor.')
    } finally {
      setTrackLoadingId(null)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center gap-4 animate-pulse">
        <div className="w-10 h-10 border-4 border-t-brand-500 border-brand-500/20 rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Synthesizing market positioning metrics...</p>
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

  // ----------------------------------------------------
  // Aggregate Insights & Compute Metrics
  // ----------------------------------------------------
  
  // 1. Social Insights
  const socialInsights = insights.filter((i) => i.insight_type === 'social')
  
  // Get latest social presence summary per competitor + platform
  const latestSocialSummaryMap: { [key: string]: Insight } = {}
  socialInsights.forEach((insight) => {
    const platform = insight.data_points?.platform
    const competitorId = insight.competitor_id
    if (platform && competitorId) {
      const key = `${competitorId}-${platform}`
      const existing = latestSocialSummaryMap[key]
      if (!existing || new Date(insight.created_at) > new Date(existing.created_at)) {
        latestSocialSummaryMap[key] = insight
      }
    }
  })
  
  const activeSocialSummaries = Object.values(latestSocialSummaryMap)

  // Compute platform averages
  const platformStats: { [platform: string]: { followers: number; engagement: number; sentiment: number; count: number } } = {}
  activeSocialSummaries.forEach((summary) => {
    const platform = summary.data_points?.platform
    if (platform) {
      if (!platformStats[platform]) {
        platformStats[platform] = { followers: 0, engagement: 0, sentiment: 0, count: 0 }
      }
      platformStats[platform].followers += summary.data_points?.follower_count || 0
      platformStats[platform].engagement += summary.data_points?.engagement_rate || 0
      platformStats[platform].sentiment += summary.sentiment_score || 0
      platformStats[platform].count += 1
    }
  })

  const aggregatedPlatforms = Object.keys(platformStats).map((platform) => {
    const stats = platformStats[platform]
    return {
      name: platform,
      avgFollowers: Math.round(stats.followers / stats.count),
      avgEngagement: stats.engagement / stats.count,
      avgSentiment: stats.sentiment / stats.count,
      totalChannels: stats.count,
    }
  })

  // 2. Unmanaged Discovered Competitors (insight_type === 'market')
  const discoveredInsightsMap: { [name: string]: Insight } = {}
  insights
    .filter((i) => i.insight_type === 'market' && i.data_points?.is_discovered)
    .forEach((insight) => {
      const name = insight.data_points?.name || insight.title
      const existing = discoveredInsightsMap[name]
      if (!existing || new Date(insight.created_at) > new Date(existing.created_at)) {
        discoveredInsightsMap[name] = insight
      }
    })

  const discoveredCompetitors = Object.values(discoveredInsightsMap)

  // 3. Competitor Matrix Mapping
  // For each tracked competitor, compute average sentiment and overall follower weight
  const competitorPositioning = competitors.map((comp) => {
    const compSummaries = activeSocialSummaries.filter((s) => s.competitor_id === comp.id)
    
    let totalFollowers = 0
    let totalSentiment = 0.0
    let totalEngagement = 0.0
    
    compSummaries.forEach((s) => {
      totalFollowers += s.data_points?.follower_count || 0
      totalSentiment += s.sentiment_score || 0.0
      totalEngagement += s.data_points?.engagement_rate || 0.0
    })

    const avgSentiment = compSummaries.length > 0 ? totalSentiment / compSummaries.length : 0.0
    const avgEngagement = compSummaries.length > 0 ? totalEngagement / compSummaries.length : 0.0
    
    // Normalize positioning coordinate variables
    // X-axis: Engagement / Market Share proxy (scaled 0 to 100 based on followers and engagement)
    // Y-axis: Brand Sentiment (scaled -1 to +1)
    const engagementScore = Math.min(100, Math.max(10, Math.log10(totalFollowers || 10) * 10 + avgEngagement * 100))

    return {
      id: comp.id,
      name: comp.name,
      followers: totalFollowers,
      sentiment: avgSentiment,
      engagement: avgEngagement,
      x: engagementScore, // 0 - 100
      y: (avgSentiment + 1) * 50, // Convert -1..1 to 0..100
    }
  })

  // Helper colors for sentiment
  const getSentimentColor = (score: number) => {
    if (score > 0.25) return 'text-emerald-400'
    if (score < -0.1) return 'text-red-400'
    return 'text-amber-400'
  }

  return (
    <div className="flex flex-col gap-8 animate-fadeIn">
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>✅</span>
            <p>{successMessage}</p>
          </div>
          <button onClick={() => setSuccessMessage('')} className="text-xs hover:underline font-semibold">Dismiss</button>
        </div>
      )}

      {/* Overview Stat Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-2 relative overflow-hidden group">
          <span className="text-2xl mb-1">🔍</span>
          <span className="text-2xl font-extrabold text-white">{discoveredCompetitors.length}</span>
          <span className="text-xs text-gray-400 font-medium">Discovered Unmanaged Competitors</span>
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-2 relative overflow-hidden group">
          <span className="text-2xl mb-1">🎭</span>
          <span className="text-2xl font-extrabold text-white">
            {aggregatedPlatforms.length > 0
              ? (aggregatedPlatforms.reduce((acc, p) => acc + p.avgSentiment, 0) / aggregatedPlatforms.length).toFixed(2)
              : '0.00'}
          </span>
          <span className="text-xs text-gray-400 font-medium">Average Market Brand Sentiment</span>
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-2 relative overflow-hidden group">
          <span className="text-2xl mb-1">🔥</span>
          <span className="text-2xl font-extrabold text-white">
            {aggregatedPlatforms.length > 0
              ? aggregatedPlatforms.sort((a, b) => b.avgFollowers - a.avgFollowers)[0]?.name.toUpperCase()
              : 'N/A'}
          </span>
          <span className="text-xs text-gray-400 font-medium">Top Brand Reach Platform</span>
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none" />
        </div>
      </div>

      {/* Matrix and Social breakdown grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Competitive Positioning Matrix */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-6">
          <div>
            <h3 className="font-bold text-white text-base">Competitive Positioning Matrix</h3>
            <p className="text-xs text-gray-400 mt-1">
              Visualizes competitor footprint strength (X-axis) against brand sentiment rating (Y-axis).
            </p>
          </div>

          {/* SVG Matrix Plot */}
          <div className="relative w-full aspect-[4/3] bg-white/2 rounded-xl border border-white/5 overflow-hidden p-6 flex flex-col">
            {/* Y Axis Label */}
            <div className="absolute left-2 top-1/2 -translate-y-1/2 -rotate-90 text-[10px] text-gray-500 font-bold uppercase tracking-wider origin-left">
              Brand Sentiment (Negative ↔ Positive)
            </div>
            
            {/* X Axis Label */}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
              Market Engagement & Presence (Low ↔ High)
            </div>

            {/* Matrix Grid Lines */}
            <div className="w-full h-full relative border-l border-b border-white/10 flex flex-col justify-between">
              {/* Horizontal grid divisions */}
              <div className="w-full border-t border-dashed border-white/5 h-0" />
              <div className="w-full border-t border-dashed border-white/5 h-0" />
              <div className="w-full border-t border-white/10 h-0" /> {/* Center line (0.0 sentiment) */}
              <div className="w-full border-t border-dashed border-white/5 h-0" />
              
              {/* Quadrant Labels */}
              <div className="absolute top-4 right-4 text-[9px] text-brand-400 font-bold uppercase tracking-widest bg-brand-500/5 px-2 py-0.5 rounded border border-brand-500/10">
                Market Leaders
              </div>
              <div className="absolute top-4 left-4 text-[9px] text-emerald-400 font-bold uppercase tracking-widest bg-emerald-500/5 px-2 py-0.5 rounded border border-emerald-500/10">
                Niche Darlings
              </div>
              <div className="absolute bottom-10 left-4 text-[9px] text-amber-500 font-bold uppercase tracking-widest bg-amber-500/5 px-2 py-0.5 rounded border border-amber-500/10">
                Underdog Threat
              </div>
              <div className="absolute bottom-10 right-4 text-[9px] text-red-400 font-bold uppercase tracking-widest bg-red-500/5 px-2 py-0.5 rounded border border-red-500/10">
                Vulnerable Giants
              </div>

              {/* Data points */}
              {competitorPositioning.map((point) => (
                <div
                  key={point.id}
                  className="absolute -translate-x-1/2 translate-y-1/2 group/point"
                  style={{ left: `${point.x}%`, bottom: `${point.y}%` }}
                >
                  <div className="w-4 h-4 rounded-full bg-brand-500 border border-white/20 shadow-[0_0_12px_rgba(139,92,246,0.5)] cursor-pointer group-hover/point:scale-125 transition-transform" />
                  
                  {/* Tooltip */}
                  <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-48 bg-dark-400 border border-white/10 p-3 rounded-xl shadow-2xl pointer-events-none opacity-0 group-hover/point:opacity-100 transition-opacity z-30">
                    <span className="font-bold text-xs text-white block mb-1">{point.name}</span>
                    <div className="flex flex-col gap-1 text-[10px] text-gray-400">
                      <div className="flex justify-between">
                        <span>Sentiment:</span>
                        <span className={`font-semibold ${getSentimentColor(point.sentiment)}`}>
                          {point.sentiment > 0 ? '+' : ''}{point.sentiment.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Followers:</span>
                        <span className="font-semibold text-white">{point.followers.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Engagement:</span>
                        <span className="font-semibold text-white">{(point.engagement * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>

                  {/* Node label */}
                  <span className="absolute left-6 -top-1 font-bold text-[10px] text-white whitespace-nowrap bg-dark-500/75 px-1.5 py-0.5 rounded border border-white/5">
                    {point.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Social Channel Analytics */}
        <div className="lg:col-span-1 glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-6">
          <div>
            <h3 className="font-bold text-white text-base">Channel Engagements</h3>
            <p className="text-xs text-gray-400 mt-1">
              Platform-level reach and user sentiment benchmarks averaged across tracked competitors.
            </p>
          </div>

          <div className="flex flex-col gap-5 flex-grow justify-center">
            {aggregatedPlatforms.length === 0 ? (
              <p className="text-xs text-gray-500 text-center py-10">No social summaries captured. Run the agent cycle to crawl channels.</p>
            ) : (
              aggregatedPlatforms.map((platform) => (
                <div key={platform.name} className="flex flex-col gap-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-sm">
                        {platform.name === 'linkedin' ? '🔗' : platform.name === 'twitter' ? '🐦' : platform.name === 'youtube' ? '📺' : platform.name === 'reddit' ? '👽' : '📱'}
                      </span>
                      <span className="font-bold text-white capitalize">{platform.name}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-[10px] text-gray-400 font-medium">{(platform.avgEngagement * 100).toFixed(1)}% Engagement</span>
                      <span className={`text-[10px] font-bold ${getSentimentColor(platform.avgSentiment)}`}>
                        {platform.avgSentiment > 0 ? '▲' : '▼'} {platform.avgSentiment.toFixed(1)}
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5">
                    <div
                      className="bg-brand-500 h-full rounded-full transition-all duration-1000"
                      style={{ width: `${Math.min(100, Math.max(5, platform.avgEngagement * 400))}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[9px] text-gray-500">
                    <span>{platform.totalChannels} channels analyzed</span>
                    <span>{platform.avgFollowers.toLocaleString()} avg followers</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Autonomous Competitor Discovery */}
      <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col gap-6">
        <div>
          <h3 className="font-bold text-white text-base">Autonomous Competitor Discovery</h3>
          <p className="text-xs text-gray-400 mt-1">
            Unmanaged competitor entities identified dynamically by Agent 4 research queries. You can promote them to active scraping.
          </p>
        </div>

        {discoveredCompetitors.length === 0 ? (
          <div className="text-center py-10 bg-white/2 border border-dashed border-white/10 rounded-xl">
            <span className="text-2xl">🌱</span>
            <p className="text-xs text-gray-500 mt-2">No unmanaged competitor profiles discovered yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {discoveredCompetitors.map((insight) => {
              const data = insight.data_points
              const isAlreadyTracked = competitors.some(
                (c) => c.name.toLowerCase() === data.name.toLowerCase() || c.website.toLowerCase() === data.website.toLowerCase()
              )

              return (
                <div
                  key={insight.id}
                  className="bg-white/2 border border-white/5 p-5 rounded-xl flex flex-col justify-between gap-4 hover:border-brand-500/20 transition-all duration-300 relative group"
                >
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <h4 className="font-bold text-white text-sm">{data.name}</h4>
                        <a
                          href={data.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                        >
                          {data.website}
                        </a>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20 text-[9px] font-bold text-brand-400">
                        {Math.round(data.confidence_score * 100)}% Match Confidence
                      </span>
                    </div>

                    <p className="text-xs text-gray-400 leading-relaxed mt-2">
                      <span className="font-bold text-gray-300 block mb-1">Target Description:</span>
                      {insight.description.split(' | Why they compete:')[0]}
                    </p>

                    <p className="text-[11px] text-gray-400 bg-white/5 border border-white/5 p-2 rounded-lg leading-relaxed mt-1">
                      <span className="font-semibold text-brand-400">Competition Reason: </span>
                      {data.match_reason}
                    </p>
                  </div>

                  <div className="flex justify-between items-center border-t border-white/5 pt-3">
                    <span className="text-[10px] text-gray-500">Discovered {new Date(insight.created_at).toLocaleDateString()}</span>
                    {isAlreadyTracked ? (
                      <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400">
                        Active Tracked
                      </span>
                    ) : (
                      <button
                        onClick={() => handleTrackCompetitor(insight.id, data.name, data.website)}
                        disabled={trackLoadingId === insight.id}
                        className="premium-btn px-4 py-1.5 rounded-lg font-bold text-white text-[10px] disabled:opacity-50"
                      >
                        {trackLoadingId === insight.id ? 'Starting Crawl...' : 'Track Competitor'}
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
