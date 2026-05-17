# WingMan - 2-Minute Pitch Script for IBM Bob Hackathon

## Opening (15 seconds)
"Hi judges! I'm [Name], and I'm here to show you **WingMan** — your AI phone proxy that handles the conversations you don't want to have.

We've all been there: you need to call your landlord about late rent, reschedule a dentist appointment, or negotiate with a recruiter. But you're anxious, busy, or just don't want to deal with it. **WingMan makes that call for you.**"

## The Problem (20 seconds)
"Phone anxiety is real. 76% of millennials avoid phone calls. But sometimes, you HAVE to call — and texting isn't an option. Current solutions? Pay a virtual assistant $30/hour, ask a friend, or procrastinate until it's too late.

**WingMan solves this with AI that sounds natural, handles back-and-forth conversations, and gives you a complete debrief afterward.**"

## The Demo Hook (10 seconds)
"Let me show you how it works. I'm going to have WingMan call a dentist to reschedule my appointment — watch how natural this is."

## Live Demo (30 seconds)
[Show AutoPilot interface]
- "I just speak: 'Call Dr. Smith's office and reschedule my 3 PM appointment to next Tuesday at 10 AM'"
- [Show voice recognition capturing the message]
- "WingMan confirms, then makes the call"
- [Show live transcript appearing in real-time]
- "Look at this — it's handling questions, confirming details, being polite"
- [Point to WhatsApp notification]
- "And I get a WhatsApp summary with action items"

## Technical Highlights (25 seconds)
"What makes this technically impressive?

**One:** Streaming LLM responses — we break AI responses into sentences and start speaking WHILE the model is still generating. This cuts latency from 3 seconds to under 1.5 seconds.

**Two:** Intelligent caller identity detection — WingMan automatically detects who answered the phone using LLM-based name extraction from natural language.

**Three:** Real-time audio pipeline — we're orchestrating Twilio WebSockets, Deepgram STT/TTS, and Groq's ultra-fast LLM inference in a single async pipeline.

**Four:** Voice-driven UX — the entire setup uses Web Speech API. No typing, no forms until you want to edit."

## The Modes (15 seconds)
"WingMan has three modes:
- **AutoPilot**: AI makes the entire call
- **Co-Pilot**: Real-time suggestions during YOUR calls — perfect for interviews or negotiations
- **Coach**: Post-call analysis with confidence scores and improvement tips"

## Market Potential (10 seconds)
"This isn't just for phone anxiety. Think customer service automation, appointment scheduling for businesses, accessibility for people with speech difficulties, or sales teams that need coaching."

## Technical Stack (10 seconds)
"Built with FastAPI, React, Twilio for telephony, Deepgram for speech, and Groq for inference. We chose Groq specifically because their LLM latency is 10x faster than OpenAI — critical for natural conversations."

## Closing (15 seconds)
"WingMan is production-ready for the demo, with comprehensive test coverage, streaming optimization, and caller identity detection — all built during this hackathon.

**We handle the conversations you don't want to have, so you don't have to.**

Questions?"

---

## Backup Talking Points (If Time Permits)

### Architecture Highlight
"Our architecture uses async Python throughout — WebSocket handlers, streaming LLM responses, and parallel TTS generation. We process sentences as they're generated, not after completion."

### Bob Integration Story
"Bob helped us optimize the streaming pipeline, design the caller identity feature, and build a comprehensive test suite. Every session is documented in our repo."

### Scalability
"Currently in-memory storage for the demo, but designed to scale with PostgreSQL, Redis caching, and message queues for production."

### Privacy & Security
"No audio recordings stored. Transcripts are temporary. WhatsApp summaries use end-to-end encryption. Production would add JWT auth and webhook signature verification."

---

## Delivery Tips
- **Energy**: High energy, confident, conversational
- **Pace**: Speak clearly but quickly — you have 2 minutes
- **Demo**: Practice the demo flow 10 times. Have backup screenshots
- **Eye Contact**: Look at judges, not the screen
- **Passion**: Show genuine excitement about solving phone anxiety
- **Technical Depth**: Balance accessibility with technical sophistication
- **Timing**: Practice with a timer. Aim for 1:50 to leave buffer for questions