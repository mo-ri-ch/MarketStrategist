'use client'

import { useState, useEffect, useRef } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────
interface Citation {
  score: number
  source_type: string
  title: string
  competitor_name?: string
  event_type?: string
  insight_type?: string
  severity?: string
  sentiment_score?: number
  created_at?: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  suggestion_cards?: string[]
  timestamp: Date
}

interface Memory {
  user_preferences?: string
  company_goals?: string
  conversation_context?: string[]
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function generateId() {
  return Math.random().toString(36).slice(2, 11)
}

function CitationBadge({ c }: { c: Citation }) {
  const [open, setOpen] = useState(false)
  const sourceColors: Record<string, string> = {
    competitor_event: 'border-amber-500/30 bg-amber-500/5 text-amber-400',
    social_insight: 'border-sky-500/30 bg-sky-500/5 text-sky-400',
    unknown: 'border-white/10 bg-white/3 text-gray-400',
  }
  const cls = sourceColors[c.source_type] ?? sourceColors.unknown
  const relevance = Math.round((c.score ?? 0) * 100)

  return (
    <div className={`rounded-xl border text-[10px] font-semibold overflow-hidden transition-all ${cls}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left"
      >
        <span className="opacity-60">{c.source_type === 'competitor_event' ? '📌' : '📊'}</span>
        <span className="truncate flex-1">{c.title}</span>
        <span className="shrink-0 opacity-60">{relevance}% match</span>
        <span className="shrink-0 opacity-50">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="px-3 pb-3 flex flex-col gap-1 border-t border-white/5 pt-2">
          {c.competitor_name && <span>Competitor: <strong>{c.competitor_name}</strong></span>}
          {c.event_type && <span>Event: {c.event_type}</span>}
          {c.insight_type && <span>Insight: {c.insight_type}</span>}
          {c.severity && <span>Severity: <span className={c.severity === 'high' ? 'text-red-400' : c.severity === 'medium' ? 'text-amber-400' : 'text-blue-400'}>{c.severity}</span></span>}
          {c.sentiment_score != null && <span>Sentiment: {c.sentiment_score.toFixed(2)}</span>}
          {c.created_at && <span className="opacity-50">{new Date(c.created_at).toLocaleDateString()}</span>}
        </div>
      )}
    </div>
  )
}

function AssistantBubble({ msg, onSuggestion }: { msg: Message; onSuggestion: (s: string) => void }) {
  return (
    <div className="flex gap-3 items-start animate-fadeIn">
      {/* Avatar */}
      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white text-sm font-bold shrink-0 shadow-lg shadow-brand-500/20">
        AI
      </div>

      <div className="flex-1 flex flex-col gap-3 max-w-[85%]">
        {/* Message bubble */}
        <div className="glass-card rounded-2xl rounded-tl-sm p-4 border border-white/5">
          <div className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
            {msg.content}
          </div>

          {/* Citations */}
          {msg.citations && msg.citations.length > 0 && (
            <div className="mt-4 flex flex-col gap-1.5">
              <span className="text-[9px] font-extrabold uppercase tracking-widest text-gray-500">
                Intelligence Sources ({msg.citations.length})
              </span>
              <div className="flex flex-col gap-1">
                {msg.citations.map((c, i) => (
                  <CitationBadge key={i} c={c} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Suggestion cards */}
        {msg.suggestion_cards && msg.suggestion_cards.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {msg.suggestion_cards.map((s, i) => (
              <button
                key={i}
                onClick={() => onSuggestion(s)}
                className="px-3 py-1.5 rounded-xl bg-brand-500/8 border border-brand-500/20 text-[10px] font-semibold text-brand-300 hover:bg-brand-500/15 hover:border-brand-500/35 transition-all"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <span className="text-[9px] text-gray-600 pl-1">
          {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  )
}

function UserBubble({ msg }: { msg: Message }) {
  return (
    <div className="flex gap-3 items-start justify-end animate-fadeIn">
      <div className="flex-1 flex flex-col items-end gap-1 max-w-[75%]">
        <div className="bg-brand-600/20 border border-brand-500/25 rounded-2xl rounded-tr-sm px-4 py-3 text-sm text-white leading-relaxed">
          {msg.content}
        </div>
        <span className="text-[9px] text-gray-600 pr-1">
          {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      <div className="w-9 h-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white text-sm font-bold shrink-0">
        👤
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3 items-start animate-fadeIn">
      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white text-sm font-bold shrink-0 shadow-lg shadow-brand-500/20">
        AI
      </div>
      <div className="glass-card rounded-2xl rounded-tl-sm px-5 py-4 border border-white/5 flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}

// ─── STARTER PROMPTS ─────────────────────────────────────────────────────────
const STARTER_PROMPTS = [
  { icon: '📊', label: 'Competitor Overview', prompt: 'Give me a summary of the latest competitor intelligence and what I should watch out for this week.' },
  { icon: '💰', label: 'Pricing Signals', prompt: 'Have any competitors changed their pricing recently? What should my response be?' },
  { icon: '📣', label: 'Social Intelligence', prompt: 'What is the current social media sentiment around our key competitors?' },
  { icon: '🚀', label: 'Strategic Moves', prompt: 'What strategic moves should I prioritize based on recent market intelligence?' },
]

// ─── MAIN PAGE ────────────────────────────────────────────────────────────────
export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [memory, setMemory] = useState<Memory>({})
  const [memoryOpen, setMemoryOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Load memory context on mount
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    fetch('http://localhost:8000/api/v1/chat/history', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => setMemory(data.memories ?? {}))
      .catch(() => {})
  }, [])

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const sendMessage = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return

    const token = localStorage.getItem('token')
    if (!token) return

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    // Build history for context
    const history = messages.map((m) => ({ role: m.role, content: m.content }))

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: trimmed, conversation_history: history }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(err.detail ?? 'Failed to get response')
      }

      const data = await res.json()

      const assistantMsg: Message = {
        id: generateId(),
        role: 'assistant',
        content: data.message ?? '',
        citations: data.citations ?? [],
        suggestion_cards: data.suggestion_cards ?? [],
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMsg])

      // Refresh memory silently after each exchange
      fetch('http://localhost:8000/api/v1/chat/history', {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then((d) => setMemory(d.memories ?? {}))
        .catch(() => {})
    } catch (err: unknown) {
      const errorMsg: Message = {
        id: generateId(),
        role: 'assistant',
        content: `⚠️ ${err instanceof Error ? err.message : 'Something went wrong. Please try again.'}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex gap-6 h-[calc(100vh-10rem)]">

      {/* ── MAIN CHAT PANEL ─────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col glass-card rounded-2xl border border-white/5 overflow-hidden">

        {/* Header */}
        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white font-bold shadow-lg shadow-brand-500/25">
              AI
            </div>
            <div>
              <p className="text-sm font-bold text-white">CEO Strategic Assistant</p>
              <p className="text-[10px] text-brand-400 font-semibold uppercase tracking-wider">
                RAG · Qdrant · Agent 8
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Online
            </span>
            <button
              onClick={() => setMemoryOpen(!memoryOpen)}
              className="px-3 py-1.5 rounded-xl bg-white/3 border border-white/8 text-[10px] font-bold text-gray-400 hover:text-white hover:border-brand-500/30 transition-all"
            >
              🧠 Memory
            </button>
          </div>
        </div>

        {/* Messages area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-5">
          {isEmpty ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-8 py-8">
              {/* Welcome */}
              <div className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-2xl mx-auto mb-4 shadow-xl shadow-brand-500/30">
                  🧠
                </div>
                <h2 className="text-lg font-bold text-white mb-1">CEO Strategic Intelligence</h2>
                <p className="text-xs text-gray-500 max-w-xs leading-relaxed">
                  Ask me about competitors, market trends, pricing shifts, or get tailored strategic advice based on your latest intelligence data.
                </p>
              </div>

              {/* Starter prompts */}
              <div className="grid grid-cols-2 gap-3 w-full max-w-lg">
                {STARTER_PROMPTS.map((p) => (
                  <button
                    key={p.prompt}
                    onClick={() => sendMessage(p.prompt)}
                    className="glass-card p-4 rounded-xl border border-white/5 flex flex-col gap-2 text-left hover:border-brand-500/25 transition-all group"
                  >
                    <span className="text-xl">{p.icon}</span>
                    <span className="text-xs font-bold text-white group-hover:text-brand-300 transition-colors">{p.label}</span>
                    <span className="text-[10px] text-gray-500 leading-relaxed line-clamp-2">{p.prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) =>
                msg.role === 'user' ? (
                  <UserBubble key={msg.id} msg={msg} />
                ) : (
                  <AssistantBubble key={msg.id} msg={msg} onSuggestion={sendMessage} />
                )
              )}
              {isLoading && <TypingIndicator />}
            </>
          )}
        </div>

        {/* Input bar */}
        <div className="px-5 py-4 border-t border-white/5 shrink-0">
          <div className="flex gap-3 items-end">
            <textarea
              id="chat-input"
              rows={1}
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                // Auto-grow
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Ask your CEO Assistant anything... (Enter to send, Shift+Enter for newline)"
              className="flex-1 input-field rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 resize-none focus:outline-none focus:border-brand-500 transition-all disabled:opacity-50"
              style={{ minHeight: '44px', maxHeight: '120px' }}
            />
            <button
              id="chat-send-btn"
              onClick={() => sendMessage(input)}
              disabled={isLoading || !input.trim()}
              className="premium-btn px-5 py-3 rounded-xl text-white text-sm font-bold flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              {isLoading ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <span>→</span>
              )}
              {isLoading ? 'Thinking' : 'Send'}
            </button>
          </div>
          <p className="text-[9px] text-gray-600 mt-2 text-center">
            Responses are AI-generated from indexed competitor intelligence. Verify before acting.
          </p>
        </div>
      </div>

      {/* ── MEMORY CONTEXT SIDEBAR ──────────────────────────────────────── */}
      <div
        className={`transition-all duration-300 shrink-0 overflow-hidden ${
          memoryOpen ? 'w-72 opacity-100' : 'w-0 opacity-0'
        }`}
      >
        <div className="w-72 glass-card rounded-2xl border border-white/5 p-5 flex flex-col gap-4 h-full overflow-y-auto">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">🧠 Agent Memory</h3>
            <button
              onClick={() => setMemoryOpen(false)}
              className="text-gray-500 hover:text-white text-xs transition-colors"
            >
              ✕
            </button>
          </div>

          <p className="text-[10px] text-gray-500 leading-relaxed">
            The assistant extracts and saves your preferences and goals automatically during conversations.
          </p>

          {/* Company Goals */}
          <div className="flex flex-col gap-2">
            <span className="text-[9px] font-extrabold uppercase tracking-widest text-brand-400">Strategic Goals</span>
            <div className="bg-brand-500/5 border border-brand-500/10 rounded-xl p-3 text-[10px] text-gray-300 leading-relaxed">
              {memory.company_goals
                ? memory.company_goals.slice(0, 300)
                : <span className="text-gray-600 italic">No goals captured yet. Tell the assistant your objectives.</span>}
            </div>
          </div>

          {/* User Preferences */}
          <div className="flex flex-col gap-2">
            <span className="text-[9px] font-extrabold uppercase tracking-widest text-amber-400">Your Preferences</span>
            <div className="bg-amber-500/5 border border-amber-500/10 rounded-xl p-3 text-[10px] text-gray-300 leading-relaxed">
              {memory.user_preferences
                ? memory.user_preferences.slice(0, 300)
                : <span className="text-gray-600 italic">No preferences captured yet.</span>}
            </div>
          </div>

          {/* Conversation context */}
          <div className="flex flex-col gap-2">
            <span className="text-[9px] font-extrabold uppercase tracking-widest text-emerald-400">
              Conversation Context ({(memory.conversation_context ?? []).length} entries)
            </span>
            <div className="flex flex-col gap-1">
              {(memory.conversation_context ?? []).slice(-5).map((ctx, i) => (
                <div
                  key={i}
                  className="bg-white/2 border border-white/5 rounded-lg p-2 text-[10px] text-gray-400 line-clamp-2"
                >
                  {ctx}
                </div>
              ))}
              {(memory.conversation_context ?? []).length === 0 && (
                <span className="text-[10px] text-gray-600 italic">No context yet.</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
