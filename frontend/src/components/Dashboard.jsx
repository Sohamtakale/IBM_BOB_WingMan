import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API = 'https://ibm-bob-wingman.onrender.com'

export default function Dashboard() {
  const navigate = useNavigate()
  const [calls, setCalls] = useState([])
  const profile = JSON.parse(localStorage.getItem('wingman_profile') || '{}')
  const firstName = profile.name?.split(' ')[0] || 'Boss'

  useEffect(() => {
    const fetch_ = () => fetch(`${API}/calls`).then(r => r.json()).then(setCalls).catch(() => {})
    fetch_()
    const id = setInterval(fetch_, 5000)
    return () => clearInterval(id)
  }, [])

  const completed = calls.filter(c => c.status === 'completed')
  const avgConfidence = completed.length
    ? Math.round(completed.reduce((s, c) => s + (c.coach_report?.confidence_score || 0), 0) / completed.length)
    : null

  return (
    <div style={{ background: '#000', minHeight: '100vh', color: '#fff' }}>

      {/* Navbar */}
      <nav style={{
        borderBottom: '1px solid #1a1a1a',
        padding: '0 48px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '58px',
        position: 'sticky',
        top: 0,
        background: '#000',
        zIndex: 10,
      }}>
        <span style={{ fontWeight: 800, fontSize: '15px', letterSpacing: '0.04em' }}>WingMan</span>
        <div style={{ display: 'flex', gap: '36px' }}>
          {['Dashboard', 'AutoPilot', 'Co-Pilot'].map((item, i) => (
            <span
              key={item}
              onClick={() => {
                if (item === 'AutoPilot') navigate('/autopilot')
                else if (item === 'Co-Pilot') navigate('/copilot')
              }}
              style={{
                fontSize: '14px',
                color: i === 0 ? '#fff' : '#555',
                cursor: 'pointer',
                borderBottom: i === 0 ? '1px solid #fff' : 'none',
                paddingBottom: '2px',
                transition: 'color 0.15s',
              }}
            >{item}</span>
          ))}
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {['🔔', '⚙️'].map(icon => (
            <div key={icon} style={{
              width: '34px', height: '34px', borderRadius: '50%',
              background: '#111', border: '1px solid #222',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '15px', cursor: 'pointer',
            }}>{icon}</div>
          ))}
          <div
            onClick={() => navigate('/onboarding')}
            style={{
              width: '34px', height: '34px', borderRadius: '50%',
              background: '#222', border: '1px solid #333',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '13px', fontWeight: 800, cursor: 'pointer',
            }}
          >{firstName[0]?.toUpperCase()}</div>
        </div>
      </nav>

      {/* Hero */}
      <div style={{ textAlign: 'center', padding: '40px 48px 0px' }}>
        <h1 style={{
          fontSize: '80px',
          fontWeight: 900,
          letterSpacing: '0.18em',
          color: '#fff',
          margin: 0,
          lineHeight: 1,
        }}>WINGMAN</h1>

        <div style={{ margin: '20px auto', maxWidth: '700px', position: 'relative' }}>
          <img
            src="/wingman2.png"
            alt="WingMan"
            style={{
              width: '100%',
              filter: 'invert(1)',
              mixBlendMode: 'screen',
              opacity: 0.95,
              display: 'block',
            }}
          />
        </div>

        <p style={{ fontSize: '18px', color: '#666', margin: '0', fontWeight: 400 }}>
          Hey {firstName}, how can I help you?
        </p>
      </div>

      {/* Module Cards */}
      <div style={{
        maxWidth: '860px',
        margin: '48px auto 0',
        padding: '0 48px',
        display: 'grid',
        gridTemplateColumns: '1.4fr 1fr',
        gap: '16px',
      }}>
        {/* AutoPilot — big card */}
        <div style={{
          background: '#0e0e0e',
          border: '1px solid #1e1e1e',
          borderRadius: '14px',
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: '#444', letterSpacing: '0.12em' }}>ACTIVE MODULE</div>
          <h2 style={{ fontSize: '30px', fontWeight: 800, color: '#fff', margin: 0 }}>AutoPilot</h2>
          <p style={{ fontSize: '14px', color: '#555', lineHeight: 1.65, flex: 1, margin: 0 }}>
            WingMan makes the call for you. Delivers your message, listens to their reply, handles everything — you just watch.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px' }}>
            <span style={{ fontSize: '12px', color: '#4ade80', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
              System Ready
            </span>
            <button
              onClick={() => navigate('/autopilot')}
              style={{
                background: '#fff', color: '#000', border: 'none',
                borderRadius: '8px', padding: '11px 22px',
                fontSize: '13px', fontWeight: 700, cursor: 'pointer',
                transition: 'background 0.15s',
              }}
            >Launch →</button>
          </div>
        </div>

        {/* Co-Pilot — smaller card */}
        <div style={{
          background: '#0e0e0e',
          border: '1px solid #1e1e1e',
          borderRadius: '14px',
          padding: '28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}>
          <div style={{ fontSize: '22px' }}>🎧</div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#fff', margin: 0 }}>Co-Pilot</h2>
          <p style={{ fontSize: '13px', color: '#555', lineHeight: 1.65, flex: 1, margin: 0 }}>
            Floats over your call. Tells you exactly what to say, live.
          </p>
          <button
            onClick={() => navigate('/copilot')}
            style={{
              background: 'transparent', color: '#fff',
              border: '1px solid #2a2a2a', borderRadius: '8px',
              padding: '10px 18px', fontSize: '13px', fontWeight: 600,
              cursor: 'pointer', marginTop: 'auto', transition: 'border-color 0.15s',
            }}
          >Activate →</button>
        </div>

        {/* Performance Coach — full width */}
        <div style={{
          gridColumn: '1 / -1',
          background: '#0e0e0e',
          border: '1px solid #1e1e1e',
          borderRadius: '14px',
          padding: '24px 28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '24px',
        }}>
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: 700, color: '#fff', margin: '0 0 6px' }}>Performance Coach</h2>
            <p style={{ fontSize: '13px', color: '#555', margin: 0 }}>
              Review past calls. See what landed, what didn't, how to be better next time.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexShrink: 0 }}>
            <div style={{
              background: '#151515', border: '1px solid #252525',
              borderRadius: '10px', padding: '14px 22px', textAlign: 'center', minWidth: '90px',
            }}>
              <div style={{ fontSize: '10px', color: '#444', letterSpacing: '0.1em', marginBottom: '6px' }}>CONFIDENCE</div>
              <div style={{ fontSize: '24px', fontWeight: 800 }}>{avgConfidence != null ? `${avgConfidence}%` : '—'}</div>
            </div>
            <div style={{
              background: '#151515', border: '1px solid #252525',
              borderRadius: '10px', padding: '14px 22px', textAlign: 'center', minWidth: '90px',
            }}>
              <div style={{ fontSize: '10px', color: '#444', letterSpacing: '0.1em', marginBottom: '6px' }}>CALLS</div>
              <div style={{ fontSize: '24px', fontWeight: 800 }}>{calls.length}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Call History */}
      <div style={{ maxWidth: '860px', margin: '40px auto 0', padding: '0 48px 80px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#fff', margin: 0 }}>Call History</h2>
          <span style={{ fontSize: '12px', color: '#444', cursor: 'pointer' }}>View all records →</span>
        </div>

        <div style={{ border: '1px solid #1a1a1a', borderRadius: '12px', overflow: 'hidden' }}>
          {calls.length === 0 ? (
            <div style={{ padding: '48px', textAlign: 'center', color: '#333', fontSize: '14px', background: '#0a0a0a' }}>
              No calls yet — launch AutoPilot to make your first one
            </div>
          ) : calls.map((call, i) => (
            <div
              key={call.call_id}
              onClick={() => call.coach_report && navigate(`/coach/${call.call_id}`)}
              style={{
                background: '#0a0a0a',
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                cursor: call.coach_report ? 'pointer' : 'default',
                borderBottom: i < calls.length - 1 ? '1px solid #141414' : 'none',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => { if (call.coach_report) e.currentTarget.style.background = '#111' }}
              onMouseLeave={e => e.currentTarget.style.background = '#0a0a0a'}
            >
              <div style={{
                width: '36px', height: '36px', borderRadius: '50%',
                background: '#151515', border: '1px solid #222',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '16px', flexShrink: 0,
              }}>📞</div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff' }}>
                  {call.call_brief?.who_calling || call.phone_number}
                </div>
                <div style={{ fontSize: '12px', color: '#444', marginTop: '2px' }}>
                  {call.phone_number} · {new Date(call.started_at || Date.now()).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
                {call.coach_report && (
                  <span style={{ fontSize: '12px', color: '#555' }}>
                    {call.coach_report.confidence_score}% confidence
                  </span>
                )}
                <span style={{
                  fontSize: '11px', padding: '4px 10px', borderRadius: '4px',
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase',
                  background: call.status === 'completed' ? 'rgba(74,222,128,0.08)'
                    : call.status === 'failed' ? 'rgba(239,68,68,0.08)'
                    : 'rgba(255,255,255,0.04)',
                  color: call.status === 'completed' ? '#4ade80'
                    : call.status === 'failed' ? '#f87171'
                    : '#555',
                }}>
                  {call.status?.replace('_', ' ')}
                </span>
                {call.coach_report && <span style={{ color: '#333', fontSize: '16px' }}>›</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid #111',
        padding: '20px 48px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: '13px', fontWeight: 700 }}>WingMan</div>
          <div style={{ fontSize: '12px', color: '#333', marginTop: '2px' }}>© 2026 WingMan AI. Your personal assistant.</div>
        </div>
        <div style={{ display: 'flex', gap: '24px' }}>
          {['Privacy Policy', 'Terms of Service', 'Support'].map(l => (
            <span key={l} style={{ fontSize: '12px', color: '#333', cursor: 'pointer' }}>{l}</span>
          ))}
        </div>
      </footer>
    </div>
  )
}
