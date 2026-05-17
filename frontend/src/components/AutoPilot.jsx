import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

const API = 'https://ibm-bob-wingman.onrender.com'
const delay = ms => new Promise(r => setTimeout(r, ms))

function ParticleOrb({ mode }) {
  const canvasRef = useRef(null)
  const rafRef = useRef(null)
  const rotRef = useRef(0)
  const modeRef = useRef(mode)
  modeRef.current = mode

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const S = 320
    canvas.width = S
    canvas.height = S
    const cx = S / 2, cy = S / 2, R = 128

    const golden = Math.PI * (3 - Math.sqrt(5))
    const pts = Array.from({ length: 750 }, (_, i) => {
      const y = 1 - (i / 749) * 2
      const r = Math.sqrt(Math.max(0, 1 - y * y))
      const theta = golden * i
      return { x: r * Math.cos(theta), y, z: r * Math.sin(theta), sz: Math.random() * 1.5 + 0.3 }
    })

    const draw = () => {
      ctx.clearRect(0, 0, S, S)
      const rot = rotRef.current
      const t = Date.now()
      const m = modeRef.current
      const pulse = m !== 'idle' ? 0.5 + 0.5 * Math.sin(t / (m === 'listening' ? 200 : 380)) : 0

      for (const p of pts) {
        const x2 = p.x * Math.cos(rot) + p.z * Math.sin(rot)
        const z2 = -p.x * Math.sin(rot) + p.z * Math.cos(rot)
        const screenX = cx + x2 * R
        const screenY = cy - p.y * R
        const depth = (z2 + 1) / 2
        const poleGlow = Math.pow(Math.abs(p.y), 0.5)
        let alpha = depth * 0.55 + poleGlow * 0.62
        if (pulse > 0) alpha *= (1 + pulse * 0.42)
        alpha = Math.min(1, Math.max(0, alpha))

        ctx.beginPath()
        ctx.arc(screenX, screenY, p.sz * (0.4 + depth * 0.6), 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255,255,255,${alpha.toFixed(2)})`
        ctx.fill()
      }

      const speeds = { idle: 0.003, listening: 0.009, speaking: 0.006, calling: 0.013 }
      rotRef.current += speeds[m] || 0.003
      rafRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => cancelAnimationFrame(rafRef.current)
  }, [])

  return <canvas ref={canvasRef} style={{ display: 'block', margin: '0 auto' }} />
}

export default function AutoPilot() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState('intro')
  const [form, setForm] = useState({ phone_number: '', who_calling: '', message: '' })
  const [callId, setCallId] = useState(null)
  const [callData, setCallData] = useState(null)
  const [wingmanText, setWingmanText] = useState('')
  const [userText, setUserText] = useState('')
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [timeoutWarning, setTimeoutWarning] = useState('')
  const transcriptRef = useRef(null)
  const formRef = useRef(form)
  const contactResolveRef = useRef(null)
  const flowStarted = useRef(false)
  const timeoutRef = useRef(null)
  formRef.current = form

  const profile = JSON.parse(localStorage.getItem('wingman_profile') || '{}')
  const firstName = (profile.name || 'there').split(' ')[0]

  const speak = useCallback(text => new Promise((resolve, reject) => {
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    setTimeoutWarning('')
    
    // Check if speech synthesis is available
    if (!window.speechSynthesis) {
      setTimeoutWarning('⚠️ Text-to-speech not available in this browser')
      setWingmanText(text)
      setTimeout(() => resolve(), 2000) // Auto-continue after showing text
      return
    }
    
    window.speechSynthesis.cancel()
    setWingmanText(text)
    setSpeaking(true)
    
    let resolved = false
    const finish = () => {
      if (resolved) return
      resolved = true
      setSpeaking(false)
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      setTimeoutWarning('')
      resolve()
    }
    
    // Set timeout for TTS (10 seconds)
    timeoutRef.current = setTimeout(() => {
      if (!resolved) {
        setTimeoutWarning('⚠️ Speech timeout - tap to continue')
        window.speechSynthesis.cancel()
        finish()
      }
    }, 10000)
    
    const utt = new SpeechSynthesisUtterance(text)
    utt.rate = 1.05
    utt.onend = finish
    utt.onerror = (e) => {
      console.error('TTS error:', e)
      setTimeoutWarning('⚠️ Speech failed - continuing...')
      finish()
    }
    
    try {
      window.speechSynthesis.speak(utt)
    } catch (e) {
      console.error('TTS speak error:', e)
      setTimeoutWarning('⚠️ Could not speak - continuing...')
      finish()
    }
  }), [])

  const listenOnce = useCallback(() => new Promise((resolve) => {
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    setTimeoutWarning('')
    
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      setTimeoutWarning('⚠️ Speech recognition not available in this browser')
      setTimeout(() => resolve(''), 2000)
      return
    }
    
    const rec = new SR()
    let final = ''
    let resolved = false
    
    const finish = (result = '') => {
      if (resolved) return
      resolved = true
      setListening(false)
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      setTimeoutWarning('')
      try {
        rec.stop()
      } catch (e) {
        // Already stopped
      }
      resolve(result)
    }
    
    // Set timeout for STT (15 seconds)
    timeoutRef.current = setTimeout(() => {
      if (!resolved) {
        setTimeoutWarning('⚠️ Listening timeout - using what I heard')
        finish(final)
      }
    }, 15000)
    
    rec.continuous = false
    rec.interimResults = true
    rec.lang = 'en-US'
    
    rec.onstart = () => {
      setListening(true)
      setUserText('')
    }
    
    rec.onresult = e => {
      const t = Array.from(e.results).map(r => r[0].transcript).join('')
      setUserText(t)
      if (e.results[e.results.length - 1].isFinal) {
        final = t
        finish(final)
      }
    }
    
    rec.onend = () => {
      finish(final)
    }
    
    rec.onerror = (e) => {
      console.error('STT error:', e)
      if (e.error === 'no-speech') {
        setTimeoutWarning('⚠️ No speech detected - try again')
      } else if (e.error === 'not-allowed') {
        setTimeoutWarning('⚠️ Microphone access denied')
      } else {
        setTimeoutWarning(`⚠️ Recognition error: ${e.error}`)
      }
      finish(final)
    }
    
    try {
      rec.start()
    } catch (e) {
      console.error('STT start error:', e)
      setTimeoutWarning('⚠️ Could not start listening')
      finish('')
    }
  }), [])

  const reListenMessage = useCallback(async () => {
    setPhase('ask_message')
    await speak(`What should I tell ${formRef.current.who_calling || 'them'}?`)
    setPhase('listen_message')
    const msg = await listenOnce()
    if (msg.trim()) setForm(f => ({ ...f, message: msg.trim() }))
    setPhase('confirm')
    const f = formRef.current
    await speak(`Got it. I'll call ${f.who_calling} and say: ${f.message || msg}. You can edit below, then tap call.`)
  }, [speak, listenOnce])

  // Main voice flow — runs once on mount
  useEffect(() => {
    if (flowStarted.current) return
    flowStarted.current = true
    ;(async () => {
      await delay(600)
      await speak(`Hey ${firstName}! Who do you want to call?`)
      setPhase('ask_who')

      const who = await listenOnce()
      if (who.trim()) setForm(f => ({ ...f, who_calling: who.trim() }))

      setPhase('contact_form')
      await new Promise(r => { contactResolveRef.current = r })

      setPhase('ask_message')
      await speak(`What should I tell ${formRef.current.who_calling || 'them'}?`)
      setPhase('listen_message')

      const msg = await listenOnce()
      if (msg.trim()) setForm(f => ({ ...f, message: msg.trim() }))

      setPhase('confirm')
      const f = formRef.current
      await speak(`Got it. I'll call ${f.who_calling} and say: ${f.message || msg}. You can edit below, then tap call.`)
    })()
  }, []) // eslint-disable-line

  // Poll during call
  useEffect(() => {
    if (!callId || phase !== 'calling') return
    const id = setInterval(async () => {
      try {
        const r = await fetch(`${API}/calls/${callId}`)
        const data = await r.json()
        setCallData(data)
        if (data.status === 'completed' || data.status === 'failed') {
          setPhase('done')
          clearInterval(id)
        }
      } catch {}
    }, 1500)
    return () => clearInterval(id)
  }, [callId, phase])

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight
    }
  }, [callData?.transcript])

  const handleContactSubmit = () => {
    if (!form.phone_number) { setError('Phone number is required.'); return }
    setError('')
    contactResolveRef.current?.()
    contactResolveRef.current = null
  }

  const handleMakeCall = async () => {
    const f = formRef.current
    if (!f.phone_number || !f.message) { setError('Number and message are required.'); return }
    setError('')
    setLoading(true)
    setTimeoutWarning('')
    window.speechSynthesis.cancel()
    
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    
    try {
      // Add fetch timeout using AbortController
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout
      
      const r = await fetch(`${API}/autopilot/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: f.phone_number,
          call_brief: {
            who_calling: f.who_calling || 'the recipient',
            goal: f.message,
            key_points: '', questions_to_ask: '', things_to_avoid: '',
            tone: profile.default_tone || 'Friendly',
          },
          user_profile: {
            name: profile.name || '', profession: profile.profession || '',
            institution: profile.institution || '',
            communication_style: profile.communication_style || 'Friendly',
            languages: profile.languages || 'English',
            default_tone: profile.default_tone || 'Friendly',
          },
        }),
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)
      const data = await r.json()
      if (!r.ok) throw new Error(data.detail || 'Failed to start call')
      setCallId(data.call_id)
      setPhase('calling')
      setWingmanText(`Calling ${f.who_calling}...`)
    } catch (e) {
      if (e.name === 'AbortError') {
        setError('Request timeout - please try again')
      } else {
        setError(e.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleEndCall = async () => {
    if (!callId) return
    await fetch(`${API}/calls/${callId}/end`, { method: 'POST' }).catch(() => {})
    setPhase('done')
  }

  const orbMode = listening ? 'listening' : speaking ? 'speaking' : phase === 'calling' ? 'calling' : 'idle'

  const DemoNote = () => (
    <div style={{
      position: 'fixed', bottom: '20px', left: '50%', transform: 'translateX(-50%)',
      background: '#0a0a0a', border: '1px solid #1e1e1e', borderRadius: '8px',
      padding: '8px 16px', maxWidth: '520px', width: 'calc(100% - 48px)',
      textAlign: 'center', zIndex: 100,
    }}>
      <span style={{ fontSize: '11px', color: '#444' }}>
        <span style={{ color: '#666', fontWeight: 600 }}>Demo:</span>
        {' '}Twilio trial only calls verified numbers.
        Use <span style={{ color: '#888', fontFamily: 'monospace' }}>+917058809304</span> or{' '}
        <span style={{ color: '#888', fontFamily: 'monospace' }}>+919579560024</span> — other numbers will fail.
      </span>
    </div>
  )

  // ---- CONTACT FORM ----
  if (phase === 'contact_form') {
    return (
      <div style={{ background: '#000', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', position: 'relative' }}>
        <button onClick={() => navigate('/dashboard')}
          style={{ position: 'absolute', top: '24px', left: '24px', background: 'transparent', border: 'none', color: '#444', fontSize: '13px', cursor: 'pointer', padding: 0 }}>
          ← Back
        </button>
        <ParticleOrb mode="idle" />
        <p style={{ color: '#555', fontSize: '13px', margin: '20px 0 20px', textAlign: 'center' }}>
          Got it. Fill in their details —
        </p>
        <div style={{ width: '100%', maxWidth: '360px', background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label>Name</label>
            <input
              value={form.who_calling}
              onChange={e => setForm(f => ({ ...f, who_calling: e.target.value }))}
              placeholder="Mom, Recruiter..."
              autoFocus
            />
          </div>
          <div>
            <label>Their number</label>
            <input
              value={form.phone_number}
              onChange={e => setForm(f => ({ ...f, phone_number: e.target.value }))}
              placeholder="+917058809304"
            />
            <p style={{ fontSize: '11px', color: '#333', margin: '5px 0 0' }}>Include country code.</p>
          </div>
          {error && <p style={{ color: '#f87171', fontSize: '13px', margin: 0 }}>{error}</p>}
          <button onClick={handleContactSubmit}
            style={{ background: '#fff', color: '#000', border: 'none', borderRadius: '8px', padding: '13px', fontSize: '14px', fontWeight: 700, cursor: 'pointer' }}>
            Continue →
          </button>
        </div>
        <DemoNote />
      </div>
    )
  }

  // ---- CONFIRM ----
  if (phase === 'confirm') {
    return (
      <div style={{ background: '#000', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', paddingBottom: '100px', position: 'relative' }}>
        <button onClick={() => navigate('/dashboard')}
          style={{ position: 'absolute', top: '24px', left: '24px', background: 'transparent', border: 'none', color: '#444', fontSize: '13px', cursor: 'pointer', padding: 0 }}>
          ← Back
        </button>
        <ParticleOrb mode={orbMode} />
        <div style={{ width: '100%', maxWidth: '400px', marginTop: '24px' }}>
          <p style={{ color: '#555', fontSize: '13px', textAlign: 'center', margin: '0 0 16px' }}>
            Here's what I'll say — edit if needed
          </p>
          <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '14px', padding: '20px', marginBottom: '12px' }}>
            <p style={{ fontSize: '10px', color: '#333', fontWeight: 700, letterSpacing: '0.1em', margin: '0 0 4px' }}>TO</p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', alignItems: 'center' }}>
              <input
                value={form.who_calling}
                onChange={e => setForm(f => ({ ...f, who_calling: e.target.value }))}
                style={{ flex: 1, background: 'transparent', border: 'none', borderBottom: '1px solid #222', color: '#fff', fontSize: '15px', fontWeight: 600, padding: '4px 0', outline: 'none', fontFamily: 'inherit' }}
              />
              <span style={{ color: '#333', fontSize: '13px' }}>·</span>
              <input
                value={form.phone_number}
                onChange={e => setForm(f => ({ ...f, phone_number: e.target.value }))}
                style={{ flex: 1, background: 'transparent', border: 'none', borderBottom: '1px solid #222', color: '#555', fontSize: '13px', padding: '4px 0', outline: 'none', fontFamily: 'inherit' }}
              />
            </div>
            <p style={{ fontSize: '10px', color: '#333', fontWeight: 700, letterSpacing: '0.1em', margin: '0 0 8px' }}>MESSAGE</p>
            <textarea
              rows={3}
              value={form.message}
              onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
              style={{ width: '100%', background: 'transparent', border: 'none', color: '#ccc', fontSize: '14px', lineHeight: 1.6, resize: 'none', outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box' }}
            />
          </div>
          {error && <p style={{ color: '#f87171', fontSize: '13px', margin: '0 0 10px' }}>{error}</p>}
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={reListenMessage}
              style={{ flex: 1, background: 'transparent', color: '#555', border: '1px solid #222', borderRadius: '8px', padding: '12px', fontSize: '13px', cursor: 'pointer' }}>
              🎙 Re-record
            </button>
            <button onClick={handleMakeCall} disabled={loading}
              style={{ flex: 2, background: loading ? '#222' : '#fff', color: loading ? '#555' : '#000', border: 'none', borderRadius: '8px', padding: '12px', fontSize: '14px', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer' }}>
              {loading ? 'Dialing...' : '📞 Call now'}
            </button>
          </div>
        </div>
        <DemoNote />
      </div>
    )
  }

  // ---- CALLING / DONE ----
  if (phase === 'calling' || phase === 'done') {
    const transcript = callData?.transcript || []
    const status = callData?.status || 'initiating'
    return (
      <div style={{ background: '#000', minHeight: '100vh', padding: '32px 24px', maxWidth: '580px', margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {phase === 'calling' ? (
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#4ade80', display: 'inline-block', animation: 'blink 1.2s ease-in-out infinite' }} />
            ) : (
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#333', display: 'inline-block' }} />
            )}
            <div>
              <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff', margin: 0 }}>
                {form.who_calling || form.phone_number}
              </h1>
              <p style={{ fontSize: '12px', color: '#444', margin: '2px 0 0' }}>
                {form.phone_number} · <span style={{ textTransform: 'capitalize' }}>{status.replace('_', ' ')}</span>
              </p>
            </div>
          </div>
          {phase === 'calling' && (
            <button onClick={handleEndCall}
              style={{ background: 'transparent', color: '#f87171', border: '1px solid #3a1a1a', borderRadius: '8px', padding: '8px 16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}>
              ⬛ End call
            </button>
          )}
          {phase === 'done' && (
            <div style={{ display: 'flex', gap: '10px' }}>
              {callId && (
                <button onClick={() => navigate(`/coach/${callId}`)}
                  style={{ background: '#fff', color: '#000', border: 'none', borderRadius: '8px', padding: '8px 16px', fontSize: '13px', fontWeight: 700, cursor: 'pointer' }}>
                  See debrief →
                </button>
              )}
              <button onClick={() => navigate('/dashboard')}
                style={{ background: 'transparent', color: '#555', border: '1px solid #222', borderRadius: '8px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer' }}>
                Dashboard
              </button>
            </div>
          )}
        </div>

        <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '16px 20px', marginBottom: '20px' }}>
          <p style={{ fontSize: '10px', color: '#333', fontWeight: 700, letterSpacing: '0.1em', margin: '0 0 6px' }}>YOUR MESSAGE</p>
          <p style={{ fontSize: '14px', color: '#fff', margin: 0 }}>{form.message}</p>
        </div>

        <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 700, color: '#fff', margin: 0 }}>Live transcript</h2>
            {phase === 'calling' && (
              <span style={{ fontSize: '11px', color: '#4ade80', display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span style={{ animation: 'blink 1.2s infinite' }}>●</span> Live
              </span>
            )}
          </div>
          <div ref={transcriptRef} style={{ maxHeight: '380px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {transcript.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#333' }}>
                {phase === 'calling' ? (
                  <>
                    <div style={{ fontSize: '28px', marginBottom: '8px' }}>📡</div>
                    <p style={{ fontSize: '13px', margin: 0 }}>Connecting... I'll start talking soon</p>
                  </>
                ) : (
                  <p style={{ fontSize: '13px', margin: 0 }}>Nothing was recorded</p>
                )}
              </div>
            ) : transcript.map((turn, i) => (
              <div key={i} style={{ display: 'flex', gap: '10px', flexDirection: turn.speaker === 'wingman' ? 'row-reverse' : 'row' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: '13px', background: turn.speaker === 'wingman' ? '#1a1a1a' : '#111', border: `1px solid ${turn.speaker === 'wingman' ? '#2a2a2a' : '#1e1e1e'}` }}>
                  {turn.speaker === 'wingman' ? '🤖' : '🧑'}
                </div>
                <div style={{ borderRadius: '10px', padding: '10px 14px', maxWidth: '75%', fontSize: '13px', color: '#ddd', lineHeight: 1.5, background: turn.speaker === 'wingman' ? '#141414' : '#0d0d0d', border: `1px solid ${turn.speaker === 'wingman' ? '#222' : '#181818'}` }}>
                  {turn.text}
                </div>
              </div>
            ))}
          </div>
        </div>

        {phase === 'done' && callData?.summary && (
          <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '20px', marginTop: '16px' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#fff', margin: '0 0 8px' }}>Done. Here's what happened —</h3>
            <p style={{ fontSize: '13px', color: '#888', margin: 0, lineHeight: 1.6 }}>{callData.summary}</p>
          </div>
        )}
        <DemoNote />
      </div>
    )
  }

  // ---- ORB SCREEN (intro / ask_who / ask_message / listen_message) ----
  return (
    <div style={{ background: '#000', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', position: 'relative' }}>
      <button onClick={() => navigate('/dashboard')}
        style={{ position: 'absolute', top: '24px', left: '24px', background: 'transparent', border: 'none', color: '#444', fontSize: '13px', cursor: 'pointer', padding: 0 }}>
        ← Back
      </button>

      <div style={{ position: 'relative' }}>
        <ParticleOrb mode={orbMode} />
        {listening && (
          <div style={{
            position: 'absolute', inset: '-12px', borderRadius: '50%',
            border: '1px solid rgba(255,255,255,0.12)',
            animation: 'orbPulse 1.4s ease-in-out infinite',
            pointerEvents: 'none',
          }} />
        )}
      </div>

      <div style={{ marginTop: '32px', textAlign: 'center', minHeight: '80px', maxWidth: '340px' }}>
        {wingmanText && (
          <p style={{ fontSize: '19px', color: '#fff', fontWeight: 600, margin: '0 0 12px', lineHeight: 1.45 }}>
            {wingmanText}
          </p>
        )}
        {userText ? (
          <p style={{ fontSize: '14px', color: '#555', margin: 0, fontStyle: 'italic' }}>
            "{userText}"
          </p>
        ) : listening ? (
          <p style={{ fontSize: '12px', color: '#2a2a2a', margin: 0, letterSpacing: '0.05em' }}>
            ● listening
          </p>
        ) : null}
        
        {/* Timeout warning display */}
        {timeoutWarning && (
          <div style={{
            marginTop: '16px',
            padding: '10px 16px',
            background: 'rgba(251, 146, 60, 0.1)',
            border: '1px solid rgba(251, 146, 60, 0.3)',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#fb923c',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}>
            {timeoutWarning}
          </div>
        )}
      </div>

      <style>{`
        @keyframes orbPulse {
          0%, 100% { transform: scale(1); opacity: 0.6; }
          50% { transform: scale(1.06); opacity: 0.15; }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
      <DemoNote />
    </div>
  )
}
