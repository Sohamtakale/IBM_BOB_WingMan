import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API = 'https://ibm-bob-wingman.onrender.com'

export default function Onboarding() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    profession: '',
    institution: '',
    communication_style: 'Direct and confident',
    languages: 'English',
    default_tone: 'Friendly',
  })
  const [saving, setSaving] = useState(false)

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const handleSave = async () => {
    if (!form.name.trim()) return alert('I need your name to get started.')
    setSaving(true)
    try {
      await fetch(`${API}/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      localStorage.setItem('wingman_profile', JSON.stringify(form))
      navigate('/dashboard')
    } catch {
      alert('Backend not running. Start it first.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ background: '#000', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
      <div style={{ width: '100%', maxWidth: '480px' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '48px', fontWeight: 900, letterSpacing: '0.15em', color: '#fff', margin: '0 0 12px' }}>WINGMAN</h1>
          <p style={{ fontSize: '15px', color: '#555', margin: 0 }}>I handle the conversations you don't want to have.</p>
        </div>

        {/* Card */}
        <div style={{ background: '#0e0e0e', border: '1px solid #1e1e1e', borderRadius: '14px', padding: '36px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#fff', margin: '0 0 6px' }}>First, who am I working for?</h2>
          <p style={{ fontSize: '13px', color: '#444', margin: '0 0 28px' }}>I'll use this every time I speak on your behalf.</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div>
              <label>Your name *</label>
              <input
                value={form.name}
                onChange={e => set('name', e.target.value)}
                placeholder="Soham"
                onKeyDown={e => e.key === 'Enter' && handleSave()}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label>What do you do?</label>
                <input value={form.profession} onChange={e => set('profession', e.target.value)} placeholder="CS Student" />
              </div>
              <div>
                <label>Where?</label>
                <input value={form.institution} onChange={e => set('institution', e.target.value)} placeholder="MIT-WPU" />
              </div>
            </div>

            <div>
              <label>How do you like to come across?</label>
              <input
                value={form.communication_style}
                onChange={e => set('communication_style', e.target.value)}
                placeholder="Confident, straight to the point"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label>Languages</label>
                <input value={form.languages} onChange={e => set('languages', e.target.value)} placeholder="English, Hindi" />
              </div>
              <div>
                <label>Default vibe</label>
                <select value={form.default_tone} onChange={e => set('default_tone', e.target.value)} style={{ appearance: 'none' }}>
                  <option>Friendly</option>
                  <option>Confident</option>
                  <option>Direct</option>
                  <option>Assertive</option>
                  <option>Professional</option>
                </select>
              </div>
            </div>
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            style={{
              width: '100%', marginTop: '28px',
              background: saving ? '#222' : '#fff',
              color: saving ? '#555' : '#000',
              border: 'none', borderRadius: '8px',
              padding: '14px', fontSize: '14px',
              fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {saving ? 'Setting up...' : "I'm your WingMan. Let's go →"}
          </button>
        </div>

        <p style={{ textAlign: 'center', color: '#2a2a2a', fontSize: '11px', marginTop: '20px' }}>
          IBM Bob Hackathon 2026
        </p>
      </div>
    </div>
  )
}
