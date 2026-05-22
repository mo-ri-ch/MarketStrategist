'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function Signup() {
  const router = useRouter()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('admin') // Default to admin for first-time builders
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // 1. Create the account
      const signupResponse = await fetch('http://localhost:8000/api/v1/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          role,
        }),
      })

      const signupData = await signupResponse.json()

      if (!signupResponse.ok) {
        throw new Error(signupData.detail || 'Failed to create account')
      }

      // 2. Perform auto-login
      const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      const loginData = await loginResponse.json()

      if (!loginResponse.ok) {
        throw new Error('Account created, but automatic login failed. Please sign in manually.')
      }

      // 3. Store credentials and go to onboarding
      localStorage.setItem('token', loginData.access_token)
      localStorage.setItem('token_type', loginData.token_type)
      localStorage.setItem('user', JSON.stringify(signupData))

      router.push('/onboarding')
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-500 px-4 py-12 relative overflow-hidden">
      {/* Dynamic Background Glows */}
      <div className="absolute top-[-25%] right-[-25%] w-[650px] h-[650px] rounded-full bg-brand-600/10 blur-[130px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-[-25%] left-[-25%] w-[600px] h-[600px] rounded-full bg-brand-800/10 blur-[150px] pointer-events-none animate-pulse duration-5000" />

      {/* Main Glassmorphic Signup Card */}
      <div className="w-full max-w-lg glass-panel p-8 md:p-10 rounded-3xl shadow-2xl relative z-10 border border-white/10">
        <div className="flex flex-col items-center gap-2 mb-8 text-center">
          <Link href="/" className="text-2xl font-bold font-sans tracking-wide gradient-text hover:opacity-90 transition-opacity">
            MarketStrategist
          </Link>
          <p className="text-gray-400 text-sm">Deploy your intelligence agents in minutes.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-red-200 text-xs flex items-center gap-2">
            <span>⚠️</span>
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Full Name</label>
            <input
              type="text"
              required
              placeholder="Sarah Jenkins"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Work Email</label>
            <input
              type="email"
              required
              placeholder="sjenkins@enterprise.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Password</label>
            <input
              type="password"
              required
              placeholder="Minimum 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Workspace Role</label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setRole('admin')}
                className={`flex flex-col items-center gap-1 p-3 rounded-xl border text-center transition-all ${
                  role === 'admin'
                    ? 'border-brand-500 bg-brand-500/10 text-white'
                    : 'border-white/5 bg-white/2 hover:bg-white/5 text-gray-400'
                }`}
              >
                <span className="text-base">🔑</span>
                <span className="text-xs font-bold">Admin</span>
                <span className="text-[9px] text-gray-400 font-medium">Full access</span>
              </button>

              <button
                type="button"
                onClick={() => setRole('planner')}
                className={`flex flex-col items-center gap-1 p-3 rounded-xl border text-center transition-all ${
                  role === 'planner'
                    ? 'border-brand-500 bg-brand-500/10 text-white'
                    : 'border-white/5 bg-white/2 hover:bg-white/5 text-gray-400'
                }`}
              >
                <span className="text-base">📅</span>
                <span className="text-xs font-bold">Planner</span>
                <span className="text-[9px] text-gray-400 font-medium">Add targets</span>
              </button>

              <button
                type="button"
                onClick={() => setRole('viewer')}
                className={`flex flex-col items-center gap-1 p-3 rounded-xl border text-center transition-all ${
                  role === 'viewer'
                    ? 'border-brand-500 bg-brand-500/10 text-white'
                    : 'border-white/5 bg-white/2 hover:bg-white/5 text-gray-400'
                }`}
              >
                <span className="text-base">👁️</span>
                <span className="text-xs font-bold">Viewer</span>
                <span className="text-[9px] text-gray-400 font-medium">Read reports</span>
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="premium-btn w-full py-3.5 mt-2 rounded-xl font-semibold text-white transition-all duration-200 hover:shadow-brand-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Creating workspace...</span>
              </>
            ) : (
              <span>Deploy Workspace</span>
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-gray-400">
          Already have an account?{' '}
          <Link href="/login" className="text-brand-400 font-semibold hover:text-brand-300 transition-colors">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  )
}
