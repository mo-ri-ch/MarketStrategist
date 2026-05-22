'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function Onboarding() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [token, setToken] = useState<string | null>(null)
  
  // Form fields
  const [name, setName] = useState('')
  const [website, setWebsite] = useState('')
  const [industry, setIndustry] = useState('')
  const [region, setRegion] = useState('')
  const [services, setServices] = useState('')
  const [goals, setGoals] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [aiSummary, setAiSummary] = useState('')

  useEffect(() => {
    // Client-side authentication check
    const storedToken = localStorage.getItem('token')
    if (!storedToken) {
      router.push('/login')
    } else {
      setToken(storedToken)
    }
  }, [router])

  const handleNext = () => {
    if (step === 1 && (!name || !website)) {
      setError('Company Name and Website are required.')
      return
    }
    setError('')
    setStep((prev) => prev + 1)
  }

  const handleBack = () => {
    setError('')
    setStep((prev) => prev - 1)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return
    setError('')
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/v1/company/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          website,
          industry,
          services,
          region,
          goals,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to onboard company')
      }

      setAiSummary(data.ai_summary || '')
      setStep(4) // Move to final step showing AI brief
    } catch (err: any) {
      setError(err.message || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-dark-500 flex items-center justify-center">
        <p className="text-gray-400">Loading workspace...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark-500 text-foreground flex flex-col relative overflow-hidden">
      {/* Decorative Glows */}
      <div className="absolute top-[-15%] right-[-10%] w-[500px] h-[500px] rounded-full bg-brand-600/10 blur-[130px] pointer-events-none" />
      <div className="absolute bottom-[-15%] left-[-10%] w-[500px] h-[500px] rounded-full bg-brand-800/10 blur-[130px] pointer-events-none" />

      {/* Header */}
      <header className="glass-panel px-6 py-4 flex items-center justify-between z-10">
        <span className="text-xl font-bold font-sans tracking-wide gradient-text">MarketStrategist</span>
        <button
          onClick={() => {
            localStorage.clear()
            router.push('/login')
          }}
          className="text-xs text-gray-400 hover:text-white transition-colors"
        >
          Sign Out
        </button>
      </header>

      {/* Form Container */}
      <main className="flex-grow flex items-center justify-center px-4 py-16 relative z-10">
        <div className="w-full max-w-2xl glass-panel p-8 md:p-10 rounded-3xl border border-white/10 shadow-2xl transition-all duration-300">
          
          {/* Stepper Header (Only show for active input steps 1 to 3) */}
          {step <= 3 && (
            <div className="flex items-center justify-between mb-10 max-w-md mx-auto">
              <div className="flex items-center gap-3">
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  step >= 1 ? 'bg-brand-500 text-white' : 'bg-white/5 text-gray-500'
                }`}>
                  1
                </span>
                <span className="text-xs font-medium text-gray-300 hidden sm:inline">Profile</span>
              </div>
              <div className="h-[1px] flex-grow bg-white/10 mx-4" />
              <div className="flex items-center gap-3">
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  step >= 2 ? 'bg-brand-500 text-white' : 'bg-white/5 text-gray-500'
                }`}>
                  2
                </span>
                <span className="text-xs font-medium text-gray-300 hidden sm:inline">Focus</span>
              </div>
              <div className="h-[1px] flex-grow bg-white/10 mx-4" />
              <div className="flex items-center gap-3">
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  step >= 3 ? 'bg-brand-500 text-white' : 'bg-white/5 text-gray-500'
                }`}>
                  3
                </span>
                <span className="text-xs font-medium text-gray-300 hidden sm:inline">Strategy</span>
              </div>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-red-200 text-xs flex items-center gap-2">
              <span>⚠️</span>
              <p>{error}</p>
            </div>
          )}

          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-center gap-6 animate-pulse">
              <div className="w-16 h-16 rounded-full border-4 border-t-brand-500 border-brand-500/20 animate-spin" />
              <div>
                <h3 className="text-lg font-bold text-white mb-2">Analyzing Company Landscape</h3>
                <p className="text-sm text-gray-400 max-w-sm">
                  Our strategic intelligence agents are parsing your profile and building your custom competitive briefing...
                </p>
              </div>
            </div>
          ) : (
            <div>
              {/* Step 1: Basic Info */}
              {step === 1 && (
                <div className="flex flex-col gap-6 animate-fadeIn">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-1.5">Introduce your company</h2>
                    <p className="text-sm text-gray-400">Let's set up the baseline details for your intelligence target.</p>
                  </div>

                  <div className="flex flex-col gap-5">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Company Name</label>
                      <input
                        type="text"
                        required
                        placeholder="Acme Corporation"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Website URL</label>
                      <input
                        type="url"
                        required
                        placeholder="https://acme.com"
                        value={website}
                        onChange={(e) => setWebsite(e.target.value)}
                        className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end mt-4">
                    <button
                      type="button"
                      onClick={handleNext}
                      className="premium-btn px-6 py-3 rounded-xl font-semibold text-white flex items-center gap-2"
                    >
                      <span>Continue</span>
                      <span>→</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Step 2: Details */}
              {step === 2 && (
                <div className="flex flex-col gap-6 animate-fadeIn">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-1.5">Define your landscape</h2>
                    <p className="text-sm text-gray-400">Specify your industry sectors and core operational regions.</p>
                  </div>

                  <div className="flex flex-col gap-5">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Industry</label>
                      <input
                        type="text"
                        placeholder="Enterprise SaaS / FinTech"
                        value={industry}
                        onChange={(e) => setIndustry(e.target.value)}
                        className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Operating Region</label>
                      <input
                        type="text"
                        placeholder="North America / Western Europe"
                        value={region}
                        onChange={(e) => setRegion(e.target.value)}
                        className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="flex justify-between mt-4">
                    <button
                      type="button"
                      onClick={handleBack}
                      className="input-field hover:bg-white/5 px-6 py-3 rounded-xl font-semibold text-white"
                    >
                      Back
                    </button>
                    <button
                      type="button"
                      onClick={handleNext}
                      className="premium-btn px-6 py-3 rounded-xl font-semibold text-white flex items-center gap-2"
                    >
                      <span>Continue</span>
                      <span>→</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Step 3: Offerings & Goals */}
              {step === 3 && (
                <form onSubmit={handleSubmit} className="flex flex-col gap-6 animate-fadeIn">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-1.5">Offerings & Objectives</h2>
                    <p className="text-sm text-gray-400">Outline services you offer and strategic goals you are tracking.</p>
                  </div>

                  <div className="flex flex-col gap-5">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Core Services & Products</label>
                      <textarea
                        rows={3}
                        placeholder="What products or services do you offer? (e.g. AI-powered lead generation, cloud CRM tooling)"
                        value={services}
                        onChange={(e) => setServices(e.target.value)}
                        className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none resize-none"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Strategic Goals</label>
                      <textarea
                        rows={3}
                        placeholder="What are your key business goals? (e.g. expand market share, introduce new AI assistant features)"
                        value={goals}
                        onChange={(e) => setGoals(e.target.value)}
                        className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none resize-none"
                      />
                    </div>
                  </div>

                  <div className="flex justify-between mt-4">
                    <button
                      type="button"
                      onClick={handleBack}
                      className="input-field hover:bg-white/5 px-6 py-3 rounded-xl font-semibold text-white"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      className="premium-btn px-6 py-3 rounded-xl font-semibold text-white flex items-center gap-2"
                    >
                      <span>Analyze Profile</span>
                      <span>✨</span>
                    </button>
                  </div>
                </form>
              )}

              {/* Step 4: AI summary briefing */}
              {step === 4 && (
                <div className="flex flex-col gap-6 animate-scaleIn">
                  <div className="text-center mb-2">
                    <span className="text-4xl">🎯</span>
                    <h2 className="text-2xl font-bold text-white mt-4 mb-1">Landscape Analysis Generated</h2>
                    <p className="text-sm text-gray-400">Our strategist agents have mapped your corporate intelligence briefing.</p>
                  </div>

                  <div className="glass-card p-6 rounded-2xl border border-brand-500/20 bg-brand-500/5 text-gray-200 text-sm leading-relaxed max-h-[300px] overflow-y-auto">
                    <p className="whitespace-pre-wrap">{aiSummary}</p>
                  </div>

                  <div className="flex flex-col gap-3 mt-4">
                    <button
                      onClick={() => router.push('/dashboard')}
                      className="premium-btn w-full py-4 rounded-xl font-semibold text-white flex items-center justify-center gap-2"
                    >
                      <span>Launch Dashboard Console</span>
                      <span>🚀</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
