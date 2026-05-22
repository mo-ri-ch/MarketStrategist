'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function Login() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Incorrect email or password')
      }

      // Store tokens
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('token_type', data.token_type)

      // Fetch user profile to see if they have any company onboarded
      const userResponse = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      })
      
      if (userResponse.ok) {
        const user = await userResponse.json()
        localStorage.setItem('user', JSON.stringify(user))
        
        // Redirect logic: we check if user has companies
        // For MVP, we will fetch companies for the user
        const companyResponse = await fetch('http://localhost:8000/api/v1/company/my-company', {
          headers: {
            'Authorization': `Bearer ${data.access_token}`
          }
        })
        
        if (companyResponse.ok) {
          const companyData = await companyResponse.json()
          if (companyData && companyData.id) {
            router.push('/dashboard')
            return
          }
        }
        
        // Default redirect to onboarding if no company exists
        router.push('/onboarding')
      } else {
        router.push('/onboarding')
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-500 px-4 relative overflow-hidden">
      {/* Dynamic Background Glows */}
      <div className="absolute top-[-20%] left-[-20%] w-[600px] h-[600px] rounded-full bg-brand-600/10 blur-[130px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[650px] h-[650px] rounded-full bg-brand-800/10 blur-[150px] pointer-events-none animate-pulse duration-5000" />

      {/* Main Glassmorphic Login Card */}
      <div className="w-full max-w-md glass-panel p-8 md:p-10 rounded-3xl shadow-2xl relative z-10 border border-white/10">
        <div className="flex flex-col items-center gap-2 mb-8 text-center">
          <Link href="/" className="text-2xl font-bold font-sans tracking-wide gradient-text hover:opacity-90 transition-opacity">
            MarketStrategist
          </Link>
          <p className="text-gray-400 text-sm">Welcome back. Access your intelligence portal.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-red-200 text-xs flex items-center gap-2 animate-shake">
            <span>⚠️</span>
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Email Address</label>
            <input
              type="email"
              required
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Password</label>
              <a href="#" className="text-xs font-medium text-brand-400 hover:text-brand-300 transition-colors">
                Forgot password?
              </a>
            </div>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="premium-btn w-full py-3.5 rounded-xl font-semibold text-white transition-all duration-200 hover:shadow-brand-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Verifying credentials...</span>
              </>
            ) : (
              <span>Sign In to Console</span>
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-gray-400">
          New to the platform?{' '}
          <Link href="/signup" className="text-brand-400 font-semibold hover:text-brand-300 transition-colors">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  )
}
