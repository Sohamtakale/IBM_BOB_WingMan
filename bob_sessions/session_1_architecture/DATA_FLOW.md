# WingMan Data Flow Diagram

## Complete Call Flow: Frontend → Twilio → Deepgram → Groq → User

This document traces the complete journey of data through the WingMan system when making an AI-powered phone call.

---

## Phase 1: Call Initiation (Frontend → Backend → Twilio)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. USER INITIATES CALL                                              │
└─────────────────────────────────────────────────────────────────────┘

[User in AutoPilot.jsx]
    │
    │ Fills form: phone_number, who_calling, message
    │ Clicks "Call now"
    │
    ▼
[POST /autopilot/start]
    │
    │ Request Body:
    │ {
    │   phone_number: "+917058809304",
    │   call_brief: {
    │     who_calling: "Mom",
    │     goal: "Tell her I'll be late for dinner",
    │     tone: "Friendly"
    │   },
    │   user_profile: { name: "Soham", ... }
    │ }
    │
    ▼
[Backend: main.py]
    │
    ├─► Generate call_id (UUID)
    │
    ├─► storage.create_call(call_id, ...)
    │   └─► Stores in _calls dict with status: INITIATING
    │
    ├─► Build webhook URL: {BASE_URL}/twilio/voice/{call_id}
    │
    └─► twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=webhook_url
        )
        │
        ▼
    [Twilio Voice API]
        │
        │ Initiates outbound call to recipient
        │ When answered, requests TwiML from webhook
        │
        ▼
    [POST /twilio/voice/{call_id}]
        │
        │ Returns TwiML:
        │ <Response>
        │   <Connect>
        │     <Stream url="wss://.../twilio/media-stream/{call_id}" />
        │   </Connect>
        │ </Response>
        │
        ▼
    [Twilio establishes WebSocket connection]
```

---

## Phase 2: WebSocket Connection & Audio Streaming

```
┌─────────────────────────────────────────────────────────────────────┐
│ 2. WEBSOCKET AUDIO PIPELINE SETUP                                   │
└─────────────────────────────────────────────────────────────────────┘

[WebSocket: /twilio/media-stream/{call_id}]
    │
    ├─► Connection accepted
    │
    ├─► storage.update_call_status(call_id, IN_PROGRESS)
    │
    ├─► Initialize queues:
    │   ├─► transcript_queue (for STT results)
    │   └─► tts_queue (for TTS audio)
    │
    ├─► Setup Deepgram STT Connection
    │   │
    │   └─► DeepgramClient.listen.live.v("1")
    │       │
    │       ├─► Model: nova-2
    │       ├─► Encoding: mulaw (8kHz)
    │       ├─► Interim results: true
    │       ├─► Endpointing: 800ms
    │       └─► Utterance end: 2500ms
    │
    ├─► Start 3 Async Tasks:
    │   │
    │   ├─► [Task 1] process_loop()
    │   │   └─► Consumes transcript_queue → LLM → tts_queue
    │   │
    │   ├─► [Task 2] tts_loop()
    │   │   └─► Consumes tts_queue → Deepgram TTS → WebSocket
    │   │
    │   └─► [Task 3] websocket_listener()
    │       └─► Receives Twilio audio → Deepgram STT
    │
    └─► Send opening message:
        │
        │ "Hi! I'm WingMan, Soham's AI assistant.
        │  Tell her I'll be late for dinner.
        │  Is there anything you'd like to say or ask Soham?"
        │
        └─► Queued to tts_queue
```

---

## Phase 3: Real-Time Conversation Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│ 3. AUDIO PROCESSING PIPELINE (During Call)                          │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ INBOUND AUDIO (Caller Speaking)                                  │
└──────────────────────────────────────────────────────────────────┘

[Caller speaks] → [Phone Network] → [Twilio]
    │
    │ WebSocket event: "media"
    │ {
    │   event: "media",
    │   media: {
    │     track: "inbound",
    │     payload: "<base64 mulaw audio>"
    │   }
    │ }
    │
    ▼
[twilio_handler.py: websocket_listener]
    │
    ├─► Decode base64 audio
    │
    └─► dg_connection.send(audio_bytes)
        │
        ▼
    [Deepgram STT - Streaming]
        │
        ├─► Interim results (partial transcripts)
        │   └─► on_transcript() callback
        │       └─► transcript_queue.put({
        │             type: "transcript",
        │             text: "I understand, what time...",
        │             is_final: false
        │           })
        │
        └─► Final result (complete utterance)
            └─► on_transcript() callback
                └─► transcript_queue.put({
                      type: "transcript",
                      text: "I understand, what time will you be home?",
                      is_final: true
                    })

┌──────────────────────────────────────────────────────────────────┐
│ LLM PROCESSING (Generating Response)                             │
└──────────────────────────────────────────────────────────────────┘

[process_loop() - Async Task]
    │
    │ Waits for final transcript from queue
    │
    ▼
[transcript_queue.get()]
    │
    │ text: "I understand, what time will you be home?"
    │ is_final: true
    │
    ▼
[storage.add_transcript_turn(call_id, "caller", text)]
    │
    ├─► Appends to call.transcript[]
    │
    └─► conversation_history.append({
          role: "user",
          content: "I understand, what time will you be home?"
        })
        │
        ▼
    [Build LLM messages]
        │
        │ messages = [
        │   {
        │     role: "system",
        │     content: "You are WingMan — a smart, warm AI assistant
        │               making a call on behalf of Soham.
        │               SITUATION: You called Mom on behalf of Soham.
        │               The message: Tell her I'll be late for dinner.
        │               HOW TO HANDLE QUESTIONS: Use common sense..."
        │   },
        │   ...last 12 conversation turns...
        │ ]
        │
        ▼
    [Groq API Call]
        │
        │ groq_client.chat.completions.create(
        │   model="llama-3.1-8b-instant",
        │   messages=messages,
        │   temperature=0.6,
        │   max_tokens=150
        │ )
        │
        ▼
    [LLM Response]
        │
        │ "He said he'll be home around 8 PM. Anything else
        │  you'd like me to pass along?"
        │
        ▼
    [storage.add_transcript_turn(call_id, "wingman", response)]
        │
        ├─► conversation_history.append({
        │     role: "assistant",
        │     content: response
        │   })
        │
        ├─► Check for goodbye:
        │   if response.endswith("goodbye"):
        │       is_goal_done = True
        │       storage.update_call_status(call_id, COMPLETING)
        │
        └─► tts_queue.put(response)

┌──────────────────────────────────────────────────────────────────┐
│ OUTBOUND AUDIO (WingMan Speaking)                                │
└──────────────────────────────────────────────────────────────────┘

[tts_loop() - Async Task]
    │
    │ Waits for text from tts_queue
    │
    ▼
[tts_queue.get()]
    │
    │ text: "He said he'll be home around 8 PM. Anything else?"
    │
    ▼
[generate_tts_audio(text)]
    │
    │ POST https://api.deepgram.com/v1/speak
    │ Headers: { Authorization: "Token {DEEPGRAM_API_KEY}" }
    │ Body: {
    │   text: "He said he'll be home around 8 PM...",
    │   model: "aura-asteria-en",
    │   encoding: "linear16",
    │   sample_rate: 8000
    │ }
    │
    ▼
[Deepgram TTS API]
    │
    │ Returns: PCM16 audio bytes (8kHz, 16-bit)
    │
    ▼
[Audio Conversion]
    │
    ├─► Ensure even byte count (for 16-bit samples)
    │
    ├─► pcm16_to_mulaw(audio_bytes)
    │   └─► audioop.lin2ulaw(pcm_data, 2)
    │       └─► Converts to 8-bit μ-law (Twilio format)
    │
    └─► Split into 160-byte chunks (20ms each)
        │
        │ for chunk in mulaw_audio (every 160 bytes):
        │
        ▼
    [Send to Twilio via WebSocket]
        │
        │ websocket.send_text(json.dumps({
        │   event: "media",
        │   streamSid: stream_sid,
        │   media: {
        │     payload: base64.encode(chunk)
        │   }
        │ }))
        │
        ▼
    [Twilio] → [Phone Network] → [Caller hears WingMan]
```

---

## Phase 4: Call Termination & Post-Processing

```
┌─────────────────────────────────────────────────────────────────────┐
│ 4. CALL END & ANALYSIS                                              │
└─────────────────────────────────────────────────────────────────────┘

[Trigger: Goodbye detected OR user clicks "End call"]
    │
    ▼
[WebSocket event: "stop" OR manual end]
    │
    ├─► Cancel async tasks (process_loop, tts_loop)
    │
    ├─► dg_connection.finish()
    │
    └─► Post-call processing:
        │
        ├─► [Generate Coach Report]
        │   │
        │   └─► coach.generate_coach_report(call_id, transcript, call_brief)
        │       │
        │       ├─► Build prompt with transcript + goals
        │       │
        │       ├─► Groq API call (llama-3.1-8b-instant)
        │       │   └─► Analyzes conversation quality
        │       │
        │       └─► Returns CoachReport:
        │           {
        │             confidence_score: 85,
        │             goal_achieved: true,
        │             goal_achievement_score: 90,
        │             what_went_well: [
        │               "Clear communication",
        │               "Polite tone maintained"
        │             ],
        │             what_to_improve: [
        │               "Could have confirmed time earlier"
        │             ],
        │             improvements: [
        │               "Ask clarifying questions upfront",
        │               "Summarize key points before ending"
        │             ],
        │             summary: "Successfully delivered message..."
        │           }
        │
        ├─► storage.save_coach_report(call_id, report)
        │
        ├─► storage.finalize_call(call_id, summary)
        │   └─► Sets status: COMPLETED, ended_at: now()
        │
        └─► [Send WhatsApp Summary]
            │
            └─► send_whatsapp_summary(call_id, call_brief, transcript, user_profile)
                │
                ├─► Build summary with Groq LLM
                │   └─► "Call with Mom is done. Message delivered OK.
                │        She said she'll keep dinner warm. She asked
                │        what time you'll be home — you need to call
                │        her back with a specific time."
                │
                └─► twilio_client.messages.create(
                      from_=WHATSAPP_FROM,
                      to=WHATSAPP_TO,
                      body=summary
                    )
                    │
                    ▼
                [User receives WhatsApp message]
```

---

## Phase 5: Frontend Updates (Real-Time Polling)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 5. FRONTEND REAL-TIME UPDATES                                       │
└─────────────────────────────────────────────────────────────────────┘

[AutoPilot.jsx - useEffect polling]
    │
    │ Every 1.5 seconds during call:
    │
    ▼
[GET /calls/{call_id}]
    │
    │ Returns current CallRecord:
    │ {
    │   call_id: "...",
    │   status: "in_progress",
    │   transcript: [
    │     { speaker: "wingman", text: "Hi! I'm WingMan...", timestamp: ... },
    │     { speaker: "caller", text: "Oh hi! What's up?", timestamp: ... },
    │     { speaker: "wingman", text: "Tell her I'll be late...", timestamp: ... },
    │     { speaker: "caller", text: "I understand, what time...", timestamp: ... },
    │     { speaker: "wingman", text: "He said around 8 PM...", timestamp: ... }
    │   ],
    │   ...
    │ }
    │
    ▼
[Frontend updates UI]
    │
    ├─► Status badge: "IN PROGRESS" (green, blinking)
    │
    ├─► Live transcript scrolls automatically
    │   └─► Shows conversation in chat-bubble format
    │
    └─► When status becomes "completed":
        │
        ├─► Stop polling
        │
        ├─► Show "See debrief →" button
        │
        └─► Display summary text
```

---

## Co-Pilot Mode Data Flow (Parallel Feature)

```
┌─────────────────────────────────────────────────────────────────────┐
│ CO-PILOT: REAL-TIME CONVERSATION ASSISTANCE                         │
└─────────────────────────────────────────────────────────────────────┘

[User in CoPilot.jsx]
    │
    ├─► Enters call brief (goal, tone)
    │
    ├─► Clicks "I'm ready. Let's go."
    │
    └─► Starts Web Speech Recognition (continuous)
        │
        ▼
    [Browser captures user's voice during their call]
        │
        │ recognition.onresult → interim & final transcripts
        │
        ▼
    [On final transcript]
        │
        │ User said: "I'm not sure about the salary range"
        │
        ▼
    [POST /copilot/suggest]
        │
        │ Request:
        │ {
        │   transcript: "I'm not sure about the salary range",
        │   call_brief: {
        │     goal: "Negotiate above ₹25L",
        │     tone: "Confident"
        │   },
        │   conversation_history: [...]
        │ }
        │
        ▼
    [Backend: copilot.py → agents/pipeline.py]
        │
        ├─► [LangGraph Node 1: Classifier]
        │   │
        │   └─► Groq LLM classifies intent
        │       └─► Returns: "question"
        │
        └─► [LangGraph Node 2: Generator]
            │
            └─► Groq LLM generates 3 suggestions:
                {
                  intent: "question",
                  suggestions: [
                    {
                      tone: "Confident",
                      text: "Based on my research and experience,
                             I'm targeting ₹28-30L. What's your range?",
                      confidence: 90
                    },
                    {
                      tone: "Diplomatic",
                      text: "I'd love to understand your budget first.
                             What range did you have in mind?",
                      confidence: 85
                    },
                    {
                      tone: "Detailed",
                      text: "Let me share my expectations. Given my
                             5 years of experience in React and Node.js,
                             plus my leadership experience, I'm looking
                             at ₹28-32L. How does that align?",
                      confidence: 80
                    }
                  ]
                }
                │
                ▼
            [Frontend displays in popup window]
                │
                └─► User sees 3 cards with different response options
                    └─► Picks one to say during their live call
```

---

## Key Data Transformations

### Audio Format Conversions
```
Caller's Voice (analog)
  → Phone Network (digital, various codecs)
  → Twilio (μ-law, 8kHz, 8-bit)
  → WebSocket (base64-encoded μ-law)
  → Backend (decoded bytes)
  → Deepgram STT (μ-law input)
  → Text transcript

Text Response
  → Deepgram TTS API
  → PCM16 audio (16-bit, 8kHz)
  → μ-law conversion (8-bit)
  → 160-byte chunks (20ms)
  → base64 encoding
  → WebSocket
  → Twilio
  → Phone Network
  → Caller hears WingMan
```

### State Transitions
```
INITIATING → IN_PROGRESS → COMPLETING → COMPLETED
                ↓
              FAILED (on error)
```

---

## Performance Characteristics

### Latency Breakdown (Typical)
- **Twilio → Backend**: ~50-100ms (WebSocket)
- **Deepgram STT**: ~200-400ms (streaming, interim results faster)
- **Groq LLM**: ~500-1000ms (Llama 3.1 8B Instant)
- **Deepgram TTS**: ~300-600ms (streaming)
- **Backend → Twilio**: ~50-100ms (WebSocket)

**Total Response Time**: ~1.1-2.2 seconds from caller finishing speech to hearing WingMan's response

### Throughput
- **Concurrent Calls**: Limited by single-instance architecture
- **WebSocket Connections**: One per active call
- **API Rate Limits**: Dependent on Groq/Deepgram tier

---

## Error Handling Flow

```
[Error Occurs]
    │
    ├─► Twilio API Error
    │   └─► storage.update_call_status(call_id, FAILED)
    │       └─► Return 500 to frontend
    │
    ├─► Deepgram STT Error
    │   └─► Log error, continue (graceful degradation)
    │
    ├─► Groq LLM Error
    │   └─► Fallback response: "I'm sorry, could you repeat that?"
    │
    ├─► TTS Error
    │   └─► Log error, skip audio (silent failure)
    │
    └─► WebSocket Disconnect
        └─► Cleanup: cancel tasks, finalize call, generate report
```

---

## Summary

The WingMan system orchestrates a complex real-time pipeline:

1. **User initiates** call via React frontend
2. **Backend coordinates** with Twilio to place call
3. **WebSocket streams** bidirectional audio
4. **Deepgram transcribes** caller's speech in real-time
5. **Groq LLM generates** contextual responses
6. **Deepgram synthesizes** speech from text
7. **Audio streams back** to caller via Twilio
8. **Post-call analysis** generates coaching insights
9. **WhatsApp summary** sent to user

All of this happens with ~1-2 second response latency, creating a natural conversation experience.