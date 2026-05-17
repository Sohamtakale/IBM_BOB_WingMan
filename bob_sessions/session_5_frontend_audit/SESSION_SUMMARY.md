# Session 5 — AutoPilot.jsx Frontend Audit

## What Bob Did
Deep audit of the AutoPilot voice-interactive component — race conditions, Web Speech API issues, and timeout UX improvements implemented.

## Voice Flow Phases
`intro` → `ask_who` → `contact_form` → `ask_message` → `listen_message` → `confirm` → `calling` → `done`

## Race Conditions Found (5)
1. Speech synthesis cancellation causing state inconsistencies
2. Contact form promise resolved twice on rapid clicks
3. Speech recognition events firing out of order
4. Multiple polling intervals created before cleanup
5. Stale form data captured by async callbacks

## Web Speech API Issues
- Firefox has no support — no fallback shown to user
- Chrome stops TTS after 15s if page is inactive
- No language config, no voice selection
- Silent failures — user sees nothing when STT/TTS fails

## Improvements Implemented
- **TTS timeout (10s)**: shows "⚠️ Speech timeout - tap to continue"
- **STT timeout (15s)**: shows "⚠️ Listening timeout - using what I heard"
- **API timeout (30s)**: AbortController on fetch calls
- Orange warning banner below orb for all timeout states
- `timeoutRef` + `timeoutWarning` state for clean lifecycle management

## Files Modified
- `frontend/src/components/AutoPilot.jsx` — timeout handling + visual warnings
- `frontend/AUTOPILOT_ANALYSIS.md` — full documentation
