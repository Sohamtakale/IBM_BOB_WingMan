import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

const API = 'http://localhost:8000'

const TONE_COLORS = {
  Confident:  { bg: '#111', border: '#333', text: '#e2e8f0', badge: '#fff' },
  Diplomatic: { bg: '#111', border: '#2a2a2a', text: '#cbd5e1', badge: '#aaa' },
  Detailed:   { bg: '#111', border: '#222', text: '#94a3b8', badge: '#777' },
}

const TONE_LABELS = {
  Confident:  'Drop it 🔥',
  Diplomatic: 'Play it smooth',
  Detailed:   'Break it down',
}

function buildPopupHTML(suggestions, intent, lastHeard, listening) {
  const cards = suggestions && suggestions.length > 0
    ? suggestions.map(s => {
        const c = TONE_COLORS[s.tone] || TONE_COLORS.Confident
        return `
          <div style="
            background:${c.bg};
            border:1px solid ${c.border};
            border-radius:12px;
            padding:12px 14px;
            margin-bottom:10px;
          ">
            <div style="color:${c.badge};font-size:11px;font-weight:700;letter-spacing:.06em;margin-bottom:6px;">
              ${({ Confident: 'DROP IT 🔥', Diplomatic: 'PLAY IT SMOOTH', Detailed: 'BREAK IT DOWN' }[s.tone] || s.tone.toUpperCase())}
            </div>
            <div style="color:${c.text};font-size:13px;line-height:1.5;">
              ${s.text}
            </div>
          </div>`
      }).join('')
    : `<div style="color:#475569;font-size:13px;text-align:center;padding:30px 0;">
         Say something. I'm right here.
       </div>`

  const intentBadge = intent
    ? `<span style="
        display:inline-block;
        background:rgba(99,102,241,0.2);
        color:#a5b4fc;
        font-size:11px;
        padding:2px 10px;
        border-radius:20px;
        margin-top:6px;
      ">${intent}</span>`
    : ''

  const dot = listening
    ? `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#4ade80;margin-right:6px;animation:blink 1.2s infinite;"></span>`
    : ''

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<title>WingMan Co-Pilot</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif; }
  body { background:#07070f; color:#f1f5f9; height:100vh; overflow:hidden; display:flex; flex-direction:column; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
  #header { background:#0d0d1a; border-bottom:1px solid #1e1e3a; padding:10px 14px; display:flex; align-items:center; justify-content:space-between; flex-shrink:0; }
  #heard-box { padding:10px 14px; border-bottom:1px solid #1e1e3a; flex-shrink:0; }
  #cards { padding:10px 14px; overflow-y:auto; flex:1; }
  ::-webkit-scrollbar { width:4px; } ::-webkit-scrollbar-thumb { background:#1e1e3a; }
</style>
</head>
<body>
  <div id="header">
    <div style="font-size:14px;font-weight:700;color:#fff;">🪽 WingMan Co-Pilot</div>
    <div style="font-size:12px;color:#4ade80;display:flex;align-items:center;">${dot}${listening ? 'Live' : 'Idle'}</div>
  </div>
  <div id="heard-box">
    <div style="font-size:10px;color:#64748b;letter-spacing:.06em;margin-bottom:4px;">HEARD</div>
    <div style="font-size:13px;color:#94a3b8;min-height:18px;">${lastHeard || 'Waiting for speech...'}</div>
    ${intentBadge}
  </div>
  <div id="cards">${cards}</div>
</body>
</html>`
}

export default function CoPilot() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState('setup')
  const [suggestions, setSuggestions] = useState(null)
  const [intent, setIntent] = useState('')
  const [listening, setListening] = useState(false)
  const [lastHeard, setLastHeard] = useState('')
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [popupOpen, setPopupOpen] = useState(false)

  const recognitionRef = useRef(null)
  const bufferRef = useRef('')
  const popupRef = useRef(null)
  const listeningRef = useRef(false)
  const silenceTimerRef = useRef(null)

  const [brief, setBrief] = useState({
    who_calling: '',
    goal: '',
    tone: 'Professional',
  })
  const set = (k, v) => setBrief(f => ({ ...f, [k]: v }))

  // Sync popup whenever suggestions / heard / intent changes
  const syncPopup = useCallback((suggs, intt, heard, live) => {
    const popup = popupRef.current
    if (!popup || popup.closed) {
      if (popupOpen) setPopupOpen(false)
      return
    }
    try {
      popup.document.open()
      popup.document.write(buildPopupHTML(suggs, intt, heard, live))
      popup.document.close()
    } catch {}
  }, [popupOpen])

  useEffect(() => {
    if (popupOpen) syncPopup(suggestions, intent, lastHeard, listening)
  }, [suggestions, intent, lastHeard, listening, popupOpen, syncPopup])

  const openPopup = () => {
    const w = 370, h = 500
    const left = window.screen.width - w - 20
    const top = 60
    const popup = window.open(
      '',
      'wingman_copilot',
      `width=${w},height=${h},top=${top},left=${left},menubar=no,toolbar=no,location=no,status=no,resizable=yes`
    )
    if (!popup) {
      setError('Popup blocked — allow popups for localhost:5173 in Chrome settings.')
      return
    }
    popupRef.current = popup
    setPopupOpen(true)
    syncPopup(suggestions, intent, lastHeard, listening)

    // Detect when user closes popup
    const checkClosed = setInterval(() => {
      if (popup.closed) {
        clearInterval(checkClosed)
        setPopupOpen(false)
        popupRef.current = null
      }
    }, 500)
  }

  const closePopup = () => {
    if (popupRef.current && !popupRef.current.closed) popupRef.current.close()
    popupRef.current = null
    setPopupOpen(false)
  }

  const fetchSuggestions = async (transcript) => {
    if (!transcript.trim()) return
    try {
      const r = await fetch(`${API}/copilot/suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript,
          call_brief: brief,
          conversation_history: history.slice(-10),
        }),
      })
      const data = await r.json()
      setSuggestions(data.suggestions)
      setIntent(data.intent)
      setHistory(h => [...h, { role: 'user', content: transcript }])
    } catch (e) {
      console.error('Suggest error', e)
    }
  }

  const startListening = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) { setError('Use Chrome — Web Speech API required.'); return }

    listeningRef.current = true
    setListening(true)

    const createRecognition = () => {
      const recognition = new SR()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'
      recognitionRef.current = recognition

      recognition.onresult = (event) => {
        let interim = '', final = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript
          if (event.results[i].isFinal) final += t
          else interim += t
        }
        const current = final || interim
        bufferRef.current = current
        setLastHeard(current)
        clearTimeout(silenceTimerRef.current)
        if (final) {
          silenceTimerRef.current = setTimeout(() => {
            fetchSuggestions(bufferRef.current)
            bufferRef.current = ''
          }, 1500)
        }
      }

      recognition.onerror = (e) => {
        if (e.error !== 'no-speech' && e.error !== 'aborted') setError(`Mic error: ${e.error}`)
      }

      // Auto-restart when tab loses focus — Chrome stops recognition on tab switch
      recognition.onend = () => {
        if (listeningRef.current) {
          setTimeout(() => {
            if (listeningRef.current) createRecognition()
          }, 300)
        }
      }

      recognition.start()
      return recognition
    }

    createRecognition()
  }

  const stopListening = () => {
    listeningRef.current = false
    clearTimeout(silenceTimerRef.current)
    recognitionRef.current?.stop()
    setListening(false)
  }

  const handleStart = () => {
    if (!brief.goal.trim()) return setError('Enter the goal of this conversation.')
    setError('')
    setPhase('active')
    startListening()
  }

  const handleStop = () => {
    stopListening()
    closePopup()
    setPhase('setup')
    setSuggestions(null)
    setLastHeard('')
    setHistory([])
    setIntent('')
    setError('')
  }

  useEffect(() => () => { recognitionRef.current?.stop(); closePopup() }, [])

  // ---- SETUP ----
  if (phase === 'setup') {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-md fade-up">
          <button onClick={() => navigate('/dashboard')} className="btn-ghost mb-6 text-sm">← Dashboard</button>

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-white mb-1">Co-Pilot</h1>
            <p className="text-slate-500 text-sm">I'll float over your call. Only you can see me.</p>
          </div>

          <div className="card p-6 space-y-4">
            <div>
              <label>Who's on the other end?</label>
              <input value={brief.who_calling} onChange={e => set('who_calling', e.target.value)}
                     placeholder="Recruiter, friend, landlord..." />
            </div>
            <div>
              <label>What are you trying to get? *</label>
              <textarea rows={2} value={brief.goal} onChange={e => set('goal', e.target.value)}
                        placeholder="Get the job offer. Negotiate above ₹25L. Don't let them lowball me." />
            </div>
            <div>
              <label>Your vibe</label>
              <select value={brief.tone} onChange={e => set('tone', e.target.value)}
                      style={{ appearance: 'none' }}>
                <option>Confident</option>
                <option>Friendly</option>
                <option>Diplomatic</option>
                <option>Assertive</option>
                <option>Professional</option>
              </select>
            </div>

            <div className="p-3 rounded-xl text-xs"
                 style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid #222', color: '#888' }}>
              Hit start → click <strong style={{color:'#ccc'}}>⧉ Pop Out</strong> → drag me over your Google Meet. I'll whisper what to say as they talk.
            </div>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <button onClick={handleStart} className="btn-primary w-full">
              I'm ready. Let's go.
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ---- ACTIVE ----
  return (
    <div className="min-h-screen p-4 max-w-lg mx-auto fade-up">
      {/* Top bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 blink" />
          <span className="text-white text-sm font-medium">I'm listening 👂</span>
        </div>
        <div className="flex gap-2">
          {!popupOpen ? (
            <button onClick={openPopup}
                    className="btn-primary text-sm px-4 py-2"
                    style={{ background: 'linear-gradient(135deg, #0891b2, #22d3ee)' }}>
              ⧉ Pop Out
            </button>
          ) : (
            <button onClick={closePopup} className="btn-ghost text-sm px-4 py-2">
              ✕ Close Float
            </button>
          )}
          <button onClick={handleStop} className="btn-danger text-sm px-4 py-2">Stop</button>
        </div>
      </div>

      {popupOpen && (
        <div className="p-3 rounded-xl mb-4 text-sm"
             style={{ background: 'rgba(34,211,238,0.08)', border: '1px solid rgba(34,211,238,0.2)', color: '#67e8f9' }}>
          I'm floating over your screen. Drag me over Google Meet. I'll update live.
        </div>
      )}

      {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

      {/* Heard */}
      <div className="card p-4 mb-4">
        <p className="text-slate-500 text-xs mb-2 uppercase tracking-wider">Heard</p>
        <p className="text-white text-sm min-h-8">
          {lastHeard || <span className="text-slate-600 italic">Waiting... 👂</span>}
        </p>
        {intent && (
          <span className="inline-block mt-2 px-2 py-0.5 rounded-full text-xs"
                style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>
            {intent}
          </span>
        )}
      </div>

      {/* Suggestions */}
      {suggestions ? (
        <div className="space-y-3">
          <p className="text-slate-500 text-xs uppercase tracking-wider">Pick your move</p>
          {suggestions.map((s, i) => {
            const c = TONE_COLORS[s.tone] || TONE_COLORS.Confident
            return (
              <div key={i} className="p-4 rounded-xl fade-up"
                   style={{ background: c.bg, border: `1px solid ${c.border}` }}>
                <div className="text-xs font-semibold mb-1" style={{ color: c.badge }}>{TONE_LABELS[s.tone] || s.tone}</div>
                <p className="text-sm leading-relaxed" style={{ color: c.text }}>{s.text}</p>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="card p-8 text-center">
          <div className="text-3xl mb-3">👂</div>
          <p className="text-slate-500 text-sm">Say something. I'm right here.</p>
        </div>
      )}

      <div className="mt-4 p-3 rounded-xl"
           style={{ background: 'rgba(34,211,238,0.06)', border: '1px solid rgba(34,211,238,0.1)' }}>
        <p className="text-slate-500 text-xs">Goal: <span className="text-cyan-300">{brief.goal}</span></p>
      </div>
    </div>
  )
}
