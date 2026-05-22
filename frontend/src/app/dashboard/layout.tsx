'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'

interface User {
  email: string
  full_name?: string
  role: string
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    
    if (!storedToken || !storedUser) {
      router.push('/login')
    } else {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
  }, [router])

  const handleLogout = () => {
    localStorage.clear()
    router.push('/login')
  }

  if (!token || !user) {
    return (
      <div className="min-h-screen bg-dark-500 flex items-center justify-center">
        <p className="text-gray-400">Loading dashboard context...</p>
      </div>
    )
  }

  const navItems = [
    { name: 'Console Overview', path: '/dashboard', icon: '📊' },
    { name: 'Tracked Competitors', path: '/dashboard/competitors', icon: '🎯' },
    { name: 'Strategic Alerts', path: '/dashboard/alerts', icon: '🔔' },
    { name: 'Market Intelligence', path: '/dashboard/market', icon: '📈' },
    { name: 'Strategic Advice', path: '/dashboard/recommendations', icon: '👔' },
    { name: 'CEO Assistant', path: '/dashboard/assistant', icon: '💬' },
  ]

  if (user && user.role === 'admin') {
    navItems.push({ name: 'System Audit Logs', path: '/dashboard/audit', icon: '📑' })
  }

  return (
    <div className="min-h-screen bg-dark-500 text-foreground flex relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-brand-600/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full bg-brand-800/5 blur-[150px] pointer-events-none" />

      {/* Sidebar */}
      <aside className="w-64 glass-panel border-r border-white/5 flex flex-col z-20 shrink-0">
        <div className="p-6 border-b border-white/5 flex flex-col gap-1">
          <Link href="/dashboard" className="text-lg font-bold font-sans tracking-wide gradient-text">
            MarketStrategist
          </Link>
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
            Agent Controller
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="flex-grow p-4 flex flex-col gap-1.5">
          {navItems.map((item) => {
            const isActive = pathname === item.path
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-brand-500/10 text-brand-300 border border-brand-500/20'
                    : 'text-gray-400 hover:text-white hover:bg-white/2 border border-transparent'
                }`}
              >
                <span className="text-base">{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>

        {/* User Identity and Logout */}
        <div className="p-4 border-t border-white/5 flex flex-col gap-3">
          <div className="flex items-center gap-3 px-2 py-1">
            <div className="w-10 h-10 rounded-full bg-brand-600 flex items-center justify-center text-white font-bold text-sm shadow-md">
              {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-bold text-white truncate">
                {user.full_name || 'Active User'}
              </span>
              <span className="text-[10px] text-brand-400 font-bold uppercase tracking-wider">
                {user.role}
              </span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full input-field hover:bg-red-950/20 hover:border-red-500/30 text-gray-400 hover:text-red-200 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2"
          >
            <span>🚪</span>
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-grow flex flex-col overflow-y-auto z-10">
        {/* Top Header */}
        <header className="glass-panel border-b border-white/5 py-4 px-8 flex justify-between items-center z-25">
          <h1 className="text-lg font-bold text-white">
            {navItems.find((item) => item.path === pathname)?.name || 'Dashboard'}
          </h1>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
              Agent Core Live
            </span>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-8 flex-grow">
          {children}
        </main>
      </div>
    </div>
  )
}
