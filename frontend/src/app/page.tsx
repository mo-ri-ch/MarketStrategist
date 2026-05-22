import Link from 'next/link'

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-dark-500 relative">
      {/* Decorative gradient glowing circles */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-brand-600/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-brand-800/10 blur-[150px] pointer-events-none" />

      {/* Header / Navbar */}
      <header className="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold font-sans tracking-wide gradient-text">MarketStrategist</span>
        </div>
        <nav className="hidden md:flex items-center gap-8 text-sm text-gray-300 font-medium">
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
          <a href="#metrics" className="hover:text-white transition-colors">Success Metrics</a>
        </nav>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium hover:text-white transition-colors">
            Sign In
          </Link>
          <Link href="/signup" className="premium-btn text-sm font-medium px-4 py-2 rounded-lg text-white">
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow flex flex-col items-center justify-center text-center px-6 py-20">
        <div className="max-w-4xl mx-auto flex flex-col items-center gap-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-brand-500/20 bg-brand-500/5 text-xs text-brand-300 font-semibold tracking-wide uppercase">
            ⚡ Powered by Multi-Agent Workflows
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight font-sans text-white leading-tight">
            Outsmart the Competition with <span className="gradient-text">AI-Driven Intel</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl leading-relaxed">
            Automatically track competitor updates, evaluate social sentiment, index industry news, and receive strategic recommendations directly from your CEO AI Assistant.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 mt-6">
            <Link href="/signup" className="premium-btn text-base font-semibold px-8 py-3 rounded-lg text-white">
              Launch Console
            </Link>
            <a href="#features" className="input-field hover:bg-white/5 transition-colors text-base font-semibold px-8 py-3 rounded-lg text-white flex items-center justify-center">
              Explore Features
            </a>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <section id="features" className="max-w-6xl mx-auto mt-32 w-full">
          <h2 className="text-3xl font-bold text-center text-white mb-4">Core Capabilities</h2>
          <p className="text-gray-400 text-center mb-16 max-w-lg mx-auto">
            Our platform deploys a highly specialized network of cooperative AI agents working 24/7.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="glass-card p-8 rounded-2xl flex flex-col gap-4 text-left">
              <div className="w-12 h-12 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-400 text-2xl font-bold">
                🌐
              </div>
              <h3 className="text-xl font-bold text-white">Web Scraping Agent</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Scrapes target websites automatically to compare page texts, detect service modifications, new offerings, and key hiring trends.
              </p>
            </div>
            <div className="glass-card p-8 rounded-2xl flex flex-col gap-4 text-left">
              <div className="w-12 h-12 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-400 text-2xl font-bold">
                📈
              </div>
              <h3 className="text-xl font-bold text-white">Social Sentiment Agent</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Monitors YouTube, LinkedIn, X, and Reddit to measure audience growth patterns, engagement scores, and overall competitor sentiment.
              </p>
            </div>
            <div className="glass-card p-8 rounded-2xl flex flex-col gap-4 text-left">
              <div className="w-12 h-12 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-400 text-2xl font-bold">
                👔
              </div>
              <h3 className="text-xl font-bold text-white">CEO Strategic Advisor</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Connects vector spaces and database profiles to generate customized strategic recommendations and answer questions in real time.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-xs text-gray-500 bg-dark-400">
        <p>&copy; {new Date().getFullYear()} MarketStrategist. All rights reserved.</p>
      </footer>
    </div>
  )
}
