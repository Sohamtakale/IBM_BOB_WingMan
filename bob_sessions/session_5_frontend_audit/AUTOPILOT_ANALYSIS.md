# AutoPilot.jsx Voice Flow Analysis

## 1. Voice Flow Phases

The component implements a 7-phase conversational flow:

### Phase Transitions:

```
intro → ask_who → contact_form → ask_message → listen_message → confirm → calling → done
```

### Detailed Phase Breakdown:

1. **intro** (lines 69, 133)
   - Initial state, 600ms delay
   - Wingman speaks: "Hey {firstName}! Who do you want to call?"
   - Transitions to `ask_who`

2. **ask_who** (line 135)
   - Calls `listenOnce()` to capture user's voice input
   - Stores result in `form.who_calling`
   - Transitions to `contact_form`

3. **contact_form** (lines 140-141, 250-289)
   - Pauses async flow using Promise + ref pattern
   - Shows UI form for phone number and name
   - User manually submits → resolves promise via `contactResolveRef`
   - Transitions to `ask_message`

4. **ask_message** (lines 143-144)
   - Wingman speaks: "What should I tell {who_calling}?"
   - Transitions to `listen_message`

5. **listen_message** (lines 145-148)
   - Calls `listenOnce()` to capture message
   - Stores result in `form.message`
   - Transitions to `confirm`

6. **confirm** (lines 150-152, 292-342)
   - Wingman speaks confirmation
   - Shows editable form with all details
   - User can re-record message or proceed to call
   - Manual action required → `handleMakeCall()` transitions to `calling`

7. **calling** (lines 216, 345-436)
   - Makes API call to start autopilot
   - Polls call status every 1.5s
   - Shows live transcript
   - Auto-transitions to `done` when call completes/fails

8. **done** (line 165, 345-436)
   - Shows final transcript and summary
   - Provides navigation to debrief or dashboard

---

## 2. Race Conditions Identified

### Critical Issues:

#### A. **Speech Synthesis Cancellation Race** (lines 89, 191)
```javascript
// In speak():
window.speechSynthesis.cancel()  // Line 89
// In handleMakeCall():
window.speechSynthesis.cancel()  // Line 191
```
**Problem:** If user clicks "Call now" while TTS is speaking, both cancel and the ongoing utterance's `onend` will fire, potentially causing state inconsistencies.

**Impact:** `setSpeaking(false)` might be called after component expects speaking to be done.

#### B. **Contact Form Promise Resolution** (lines 141, 182-183)
```javascript
await new Promise(r => { contactResolveRef.current = r })
// Later:
contactResolveRef.current?.()
contactResolveRef.current = null
```
**Problem:** If user rapidly clicks "Continue" multiple times, the ref might be null when trying to resolve, or resolve multiple times.

**Impact:** Flow might hang or skip phases.

#### C. **Listening State Race** (lines 106-114)
```javascript
rec.onstart = () => { setListening(true); setUserText('') }
rec.onresult = e => { /* ... */ if (isFinal) rec.stop() }
rec.onend = () => { setListening(false); resolve(final) }
rec.onerror = () => { setListening(false); resolve(final) }
```
**Problem:** If recognition errors occur before `onstart`, or if `stop()` is called before `onstart` fires, state can be inconsistent.

**Impact:** UI might show "listening" when not actually listening, or vice versa.

#### D. **Call Polling Cleanup** (lines 157-171)
```javascript
const id = setInterval(async () => { /* poll */ }, 1500)
return () => clearInterval(id)
```
**Problem:** If `callId` or `phase` changes rapidly, multiple intervals might be created before cleanup runs.

**Impact:** Multiple polling requests, wasted resources.

#### E. **Form Ref Staleness** (lines 80-83, 124, 144, 152, 187)
```javascript
const formRef = useRef(form)
formRef.current = form
```
**Problem:** `formRef.current` is updated on every render, but async callbacks capture the ref, not the value. If form changes during async operations, callbacks see stale data.

**Impact:** Wrong data might be used in API calls or speech.

---

## 3. Web Speech API Cross-Browser Issues

### Current Implementation Problems:

#### A. **Browser Support Check** (line 100)
```javascript
const SR = window.SpeechRecognition || window.webkitSpeechRecognition
if (!SR) { resolve(''); return }
```
**Issues:**
- ✅ Good: Checks for webkit prefix
- ❌ Missing: No user feedback when API unavailable
- ❌ Missing: No check for `speechSynthesis` availability
- ❌ Missing: Firefox doesn't support Web Speech API at all

#### B. **Speech Recognition Configuration** (lines 104-105)
```javascript
rec.continuous = false
rec.interimResults = true
```
**Issues:**
- ✅ Good: `continuous: false` for single utterance
- ⚠️ Partial: `interimResults: true` works but can cause UI flicker
- ❌ Missing: No `lang` property set (defaults to browser language)
- ❌ Missing: No `maxAlternatives` set

#### C. **Speech Synthesis** (lines 92-96)
```javascript
const utt = new SpeechSynthesisUtterance(text)
utt.rate = 1.05
utt.onend = () => { setSpeaking(false); resolve() }
utt.onerror = () => { setSpeaking(false); resolve() }
window.speechSynthesis.speak(utt)
```
**Issues:**
- ❌ Missing: No voice selection (uses default, which varies by browser)
- ❌ Missing: No `pitch` or `volume` configuration
- ❌ Missing: Chrome has a bug where synthesis stops after 15 seconds if page is inactive
- ❌ Missing: No check if voices are loaded (`speechSynthesis.getVoices()`)

#### D. **Error Handling** (lines 95, 113)
```javascript
utt.onerror = () => { setSpeaking(false); resolve() }
rec.onerror = () => { setListening(false); resolve(final) }
```
**Issues:**
- ❌ Silent failures: Errors are swallowed, user sees nothing
- ❌ No error type checking (network, aborted, not-allowed, etc.)
- ❌ No retry logic

---

## 4. Loading State Issues

### Current Problems:

1. **No TTS Timeout** (lines 88-97)
   - If `speechSynthesis.speak()` hangs, user sees orb spinning forever
   - No visual indication that something is wrong

2. **No STT Timeout** (lines 99-115)
   - If `recognition.start()` hangs or never fires `onend`, flow stops
   - User sees "listening" indicator indefinitely

3. **No API Call Timeout** (lines 193-212)
   - `fetch()` has no timeout, can hang indefinitely
   - Only shows "Dialing..." during the call, not during network wait

4. **No Feedback During Delays** (line 133)
   - 600ms delay at start has no loading indicator
   - User sees blank screen

---

## 5. Recommended Improvements

### High Priority:

1. **Add timeout wrappers for TTS/STT**
2. **Add visual timeout fallback UI**
3. **Improve error handling with user feedback**
4. **Add browser compatibility checks**
5. **Fix race conditions in async flow**

### Medium Priority:

6. **Add retry logic for failed operations**
7. **Improve form validation**
8. **Add language configuration**
9. **Add voice selection for TTS**

### Low Priority:

10. **Add analytics/logging**
11. **Add keyboard shortcuts**
12. **Improve accessibility (ARIA labels)**