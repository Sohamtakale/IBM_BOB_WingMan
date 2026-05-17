import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

const API = 'https://ibm-bob-wingman.onrender.com'

function ScoreRing({ score, color }) {
  const r = 36
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ

  return (
    <svg width="90" height="90" style={{ transform: 'rotate(-90deg)' }}>
      <circle cx="45" cy="45" r={r} fill="none" stroke="#1a1a1a" strokeWidth="8" />
      <circle cx="45" cy="45" r={r} fill="none" stroke={color} strokeWidth="8"
              strokeDasharray={circ} strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1s ease' }} />
      <text x="45" y="49" textAnchor="middle"
            style={{ fill: 'white', fontSize: '16px', fontWeight: '700', transform: 'rotate(90deg)', transformOrigin: '45px 45px' }}>
        {score}
      </text>
    </svg>
  )
}

export default function CoachReport() {
  const { callId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [call, setCall] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const [callRes, reportRes] = await Promise.all([
          fetch(`${API}/calls/${callId}`),
          fetch(`${API}/calls/${callId}/coach`),
        ])
        if (callRes.ok) setCall(await callRes.json())
        if (reportRes.ok) setReport(await reportRes.json())
        else setError('Debrief not ready yet.')
      } catch {
        setError('Could not load. Is the backend running?')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [callId])

  if (loading) {
    return (
      <div style={{ background: '#000', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#444', fontSize: '14px' }}>Analyzing the call...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ background: '#000', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#f87171', marginBottom: '16px' }}>{error}</p>
          <button onClick={() => navigate('/dashboard')} className="btn-ghost">← Back</button>
        </div>
      </div>
    )
  }

  const scoreColor = report.confidence_score >= 70 ? '#fff' : report.confidence_score >= 45 ? '#aaa' : '#555'
  const goalColor = report.goal_achieved ? '#4ade80' : '#f87171'

  return (
    <div style={{ background: '#000', minHeight: '100vh', padding: '32px 24px', maxWidth: '640px', margin: '0 auto' }}>

      <button onClick={() => navigate('/dashboard')}
        style={{ background: 'transparent', border: 'none', color: '#444', fontSize: '13px', cursor: 'pointer', marginBottom: '28px', padding: 0 }}>
        ← Back
      </button>

      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 800, color: '#fff', margin: '0 0 6px' }}>Here's the debrief.</h1>
        <p style={{ fontSize: '13px', color: '#444', margin: 0 }}>
          {call?.detected_caller_name ? (
            <>
              <span style={{ color: '#4ade80' }}>{call.detected_caller_name}</span>
              {call?.call_brief?.who_calling && call.detected_caller_name !== call.call_brief.who_calling &&
                <span style={{ color: '#666' }}> (expected: {call.call_brief.who_calling})</span>
              }
              {' · '}{call?.phone_number}
            </>
          ) : (
            <>
              {call?.call_brief?.who_calling && `${call.call_brief.who_calling} · `}{call?.phone_number}
            </>
          )}
        </p>
      </div>

      {/* Score cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <ScoreRing score={report.confidence_score} color={scoreColor} />
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#fff' }}>Your energy</div>
            <div style={{ fontSize: '12px', color: '#444', marginTop: '4px' }}>How confident you came across</div>
          </div>
        </div>
        <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <ScoreRing score={report.goal_achievement_score} color={goalColor} />
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#fff' }}>Did we get it?</div>
            <div style={{ fontSize: '12px', marginTop: '4px', fontWeight: 600, color: report.goal_achieved ? '#4ade80' : '#f87171' }}>
              {report.goal_achieved ? 'Got it ✓' : 'Not this time ✗'}
            </div>
          </div>
        </div>
      </div>

      {/* Summary */}
      {report.summary && (
        <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '20px', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '11px', fontWeight: 700, color: '#444', letterSpacing: '0.1em', margin: '0 0 10px' }}>WHAT HAPPENED</h3>
          <p style={{ fontSize: '14px', color: '#ccc', lineHeight: 1.65, margin: 0 }}>{report.summary}</p>
        </div>
      )}

      {/* What you crushed */}
      <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '20px', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#4ade80', margin: '0 0 14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          ✓ What you crushed
        </h3>
        {report.what_went_well?.length > 0 ? (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {report.what_went_well.map((item, i) => (
              <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '13px', color: '#aaa' }}>
                <span style={{ color: '#4ade80', marginTop: '2px', flexShrink: 0 }}>•</span>
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ fontSize: '13px', color: '#333', margin: 0 }}>Nothing stood out yet — make more calls.</p>
        )}
      </div>

      {/* Real talk */}
      <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '20px', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#f87171', margin: '0 0 14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          ✗ Real talk
        </h3>
        {report.what_to_improve?.length > 0 ? (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {report.what_to_improve.map((item, i) => (
              <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '13px', color: '#aaa' }}>
                <span style={{ color: '#f87171', marginTop: '2px', flexShrink: 0 }}>•</span>
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ fontSize: '13px', color: '#333', margin: 0 }}>No weak spots. Solid.</p>
        )}
      </div>

      {/* Next time */}
      <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '20px', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#fff', margin: '0 0 14px' }}>Next time, try this —</h3>
        {report.improvements?.length > 0 ? (
          <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {report.improvements.slice(0, 3).map((item, i) => (
              <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <span style={{
                  width: '22px', height: '22px', borderRadius: '50%',
                  background: '#1a1a1a', border: '1px solid #2a2a2a',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '11px', fontWeight: 800, color: '#fff', flexShrink: 0,
                }}>{i + 1}</span>
                <span style={{ fontSize: '13px', color: '#aaa', lineHeight: 1.6 }}>{item}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p style={{ fontSize: '13px', color: '#333', margin: 0 }}>Nothing to add.</p>
        )}
      </div>

      {/* Transcript */}
      {call?.transcript?.length > 0 && (
        <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ fontSize: '11px', fontWeight: 700, color: '#333', letterSpacing: '0.1em', margin: '0 0 14px' }}>THE WHOLE CONVERSATION</h3>
          <div style={{ maxHeight: '260px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {call.transcript.map((turn, i) => (
              <div key={i} style={{ display: 'flex', gap: '10px', fontSize: '13px' }}>
                <span style={{ fontWeight: 700, width: '60px', flexShrink: 0, color: turn.speaker === 'wingman' ? '#fff' : '#555' }}>
                  {turn.speaker === 'wingman' ? 'WingMan' : 'Them'}
                </span>
                <span style={{ color: '#888', lineHeight: 1.5 }}>{turn.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
