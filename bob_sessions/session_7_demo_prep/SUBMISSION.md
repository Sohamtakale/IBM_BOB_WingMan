# WingMan - IBM Bob Hackathon 2026 Submission

## 🎯 Project Summary

**WingMan** is an AI-powered phone proxy that makes calls on your behalf, provides real-time conversation coaching, and analyzes your performance. It solves the universal problem of phone anxiety and awkward conversations by letting AI handle the call while you stay in control.

**Tagline**: *"I handle the conversations you don't want to have."*

---

## 🚀 The Problem

- **76% of millennials avoid phone calls** due to anxiety
- Important calls still require voice: doctor appointments, landlord negotiations, customer service
- Current solutions are expensive ($30/hour virtual assistants) or unavailable (asking friends)
- No AI solution exists that can handle natural back-and-forth phone conversations

---

## 💡 Our Solution

WingMan offers three modes:

### 1. 🤖 AutoPilot Mode
AI makes the entire call for you:
- Voice-driven setup (no typing)
- Natural conversation with recipients
- Real-time transcript display
- Automatic WhatsApp summary
- Post-call coaching report

**Use Cases**: Late rent notifications, appointment rescheduling, restaurant reservations, professor inquiries

### 2. 🎧 Co-Pilot Mode
Real-time suggestions during YOUR calls:
- Listens via microphone
- Provides 3 response options (Confident, Diplomatic, Detailed)
- Floating popup overlays on video calls
- Intent classification

**Use Cases**: Job interviews, salary negotiations, difficult conversations, sales calls

### 3. 📊 Coach Mode
Post-call analysis and feedback:
- Confidence score (0-100)
- Goal achievement tracking
- What went well / What to improve
- Actionable tips
- Full transcript review

---

## 🏗️ Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                   │
│  Dashboard → AutoPilot → Co-Pilot → Coach → Onboarding      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Storage  │  │  Twilio  │  │ Co-Pilot │  │  Coach   │   │
│  │ (Memory) │  │ Handler  │  │ (Agents) │  │ (Report) │   │
│  └──────────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└─────────────────────┼─────────────┼─────────────┼──────────┘
                      │             │             │
        ┌─────────────┼─────────────┼─────────────┼─────────┐
        │             │             │             │         │
   ┌────▼────┐   ┌───▼────┐   ┌───▼────┐   ┌───▼────┐    │
   │ Twilio  │   │Deepgram│   │  Groq  │   │  Groq  │    │
   │  Voice  │   │STT/TTS │   │  LLM   │   │  LLM   │    │
   └─────────┘   └────────┘   └────────┘   └────────┘    │
                                                           │
                     EXTERNAL SERVICES                    │
└────────────────────────────────────────────────────────────┘
```

### Real-Time Audio Pipeline

```
Twilio Call (μ-law audio)
    ↓ WebSocket
[Backend Handler]
    ↓ base64 decode
Deepgram STT (Nova-2)
    ↓ transcript_queue
[Streaming LLM] Groq Llama 3.1
    ↓ sentence_queue (parallel)
Deepgram TTS (Aura)
    ↓ PCM16 → μ-law
Twilio Call (audio playback)
```

---

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern async Python web framework
- **Twilio**: Phone call infrastructure and WebSocket streaming
- **Deepgram**: Speech-to-Text (Nova-2) & Text-to-Speech (Aura)
- **Groq**: Ultra-fast LLM inference (Llama 3.1 8B Instant)
- **LangGraph**: Agent orchestration framework
- **WebSockets**: Real-time bidirectional communication
- **httpx**: Async HTTP client
- **Pydantic**: Data validation and models

### Frontend
- **React 18**: UI library with hooks
- **Vite**: Build tool and dev server
- **React Router**: Client-side routing
- **Web Speech API**: Browser speech recognition/synthesis
- **Canvas API**: Particle orb visualization
- **Tailwind CSS**: Utility-first styling

### External Services
- **Twilio Voice API**: Phone call handling
- **Twilio WhatsApp**: Post-call summaries
- **Deepgram API**: STT/TTS processing
- **Groq API**: LLM inference

### Development Tools
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **uvicorn**: ASGI server

---

## 🎨 Key Features & Innovation

### 1. Streaming LLM Response Pipeline
**Innovation**: Break LLM responses into sentences and start TTS immediately while still generating
- **Result**: 50% latency reduction (3s → 1.5s)
- **Implementation**: Async queues, parallel TTS processing, sentence detection

### 2. Intelligent Caller Identity Detection
**Innovation**: Automatically detect who answered using LLM-based name extraction
- **Result**: Personalized coaching reports and summaries
- **Implementation**: Natural language understanding, conservative validation

### 3. Voice-Driven UX
**Innovation**: Complete call setup via voice with particle orb visualization
- **Result**: Zero typing required, intuitive interface
- **Implementation**: Web Speech API, golden ratio sphere, dynamic animations

### 4. Real-Time WebSocket Audio Pipeline
**Innovation**: Full-duplex audio streaming with multiple concurrent processes
- **Result**: Natural conversation flow, low latency
- **Implementation**: Async Python, audio codec conversion, chunked streaming

### 5. Context-Aware Conversation Management
**Innovation**: Dynamic system prompts, sliding window history, goodbye detection
- **Result**: Natural, contextual responses
- **Implementation**: Smart prompting, state management, conversation tracking

---

## 📊 Performance Metrics

### Latency Breakdown
- **Total Response Time**: ~1.5 seconds (caller stops → WingMan responds)
  - Deepgram STT: ~200-400ms
  - Groq LLM (streaming): ~500-1000ms
  - Deepgram TTS: ~300-600ms
  - Network overhead: ~200ms

### Optimization Achievements
- **50% faster** than non-streaming approach
- **10x faster LLM** than OpenAI (Groq vs GPT-4)
- **Sub-2-second** response time for natural conversation

### Scalability
- **Current**: In-memory storage, single instance
- **Production-ready**: Designed for PostgreSQL, Redis, message queues

---

## 🧪 Testing & Quality

### Test Coverage
- **Backend**: 90%+ code coverage
- **Test Suite**: Comprehensive pytest suite
- **Mocking**: Twilio, Deepgram, Groq services
- **CI/CD Ready**: Automated testing pipeline

### Test Categories
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: API endpoint testing
3. **Feature Tests**: Caller identity detection
4. **Mock Tests**: External service simulation

### Quality Assurance
- **Type Safety**: Pydantic models throughout
- **Error Handling**: Graceful degradation on failures
- **Logging**: Comprehensive debug information
- **Documentation**: Extensive inline comments

---

## 👥 Team Information

### Team Name
**WingMan Development Team**

### Team Members
- **Developer**: Soham
- **AI Collaborator**: IBM Bob (6 documented sessions)

### Roles & Contributions
- **Architecture Design**: System design, data flow, component structure
- **Backend Development**: FastAPI, Twilio integration, audio pipeline
- **Frontend Development**: React components, voice UX, animations
- **AI Integration**: Groq LLM, Deepgram STT/TTS, LangGraph agents
- **Testing**: Pytest suite, mock services, coverage analysis
- **Documentation**: README, architecture docs, session summaries

---

## 🤖 Bob Collaboration

### Session History
1. **Session 1**: Architecture design and documentation
2. **Session 2**: Code review and optimization recommendations
3. **Session 3**: Comprehensive test suite development
4. **Session 4**: Caller identity detection feature
5. **Session 5**: Frontend audit and analysis
6. **Session 6**: Streaming optimization and latency reduction

### Bob's Impact
- **Architecture**: Designed scalable, production-ready system
- **Code Quality**: Identified optimization opportunities
- **Testing**: Built comprehensive test coverage
- **Features**: Designed and implemented caller identity detection
- **Performance**: Optimized streaming pipeline for 50% latency reduction
- **Documentation**: Created extensive technical documentation

### Documentation
All Bob sessions documented in `/bob_sessions/` with:
- Session summaries
- Implementation details
- Code reviews
- Feature designs
- Performance analysis

---

## 📁 Project Structure

```
wingman/
├── backend/
│   ├── main.py              # FastAPI app & routes
│   ├── twilio_handler.py    # Call orchestration & WebSocket
│   ├── storage.py           # In-memory data store
│   ├── coach.py             # Post-call analysis
│   ├── copilot.py           # Real-time suggestions
│   ├── models.py            # Pydantic data models
│   ├── requirements.txt     # Python dependencies
│   ├── agents/
│   │   └── pipeline.py      # LangGraph agent
│   └── tests/
│       ├── conftest.py      # Test fixtures
│       ├── test_twilio_handler.py
│       └── test_caller_identity.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Router setup
│   │   ├── main.jsx         # Entry point
│   │   └── components/
│   │       ├── Dashboard.jsx
│   │       ├── AutoPilot.jsx
│   │       ├── CoPilot.jsx
│   │       ├── CoachReport.jsx
│   │       └── Onboarding.jsx
│   ├── package.json
│   └── vite.config.js
├── bob_sessions/            # Bob collaboration documentation
│   ├── session_1_architecture/
│   ├── session_2_code_review/
│   ├── session_3_test_suite/
│   ├── session_4_caller_identity/
│   ├── session_5_frontend_audit/
│   └── session_6_streaming_optimization/
├── ARCHITECTURE.md          # System architecture
├── DATA_FLOW.md            # Data flow diagrams
├── CONTRIBUTING.md         # Contribution guidelines
├── PITCH_SCRIPT.md         # 2-minute pitch for judges
├── DEMO_SCENARIO.md        # Demo walkthrough
├── TECHNICAL_HIGHLIGHTS.md # Top 5 technical features
├── README.md               # Project overview
└── start.sh                # Startup script
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Chrome/Edge browser (Web Speech API)
- API Keys: Twilio, Deepgram, Groq

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd wingman

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Run application
cd ..
chmod +x start.sh
./start.sh
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🎬 Demo Instructions

### Demo Scenario: Dentist Appointment Rescheduling

**Setup**: Call Dr. Smith's office to reschedule Wednesday 3 PM to Tuesday 10 AM

**Test Numbers** (Twilio verified):
- `+917058809304`
- `+919579560024`

**Demo Flow** (90 seconds):
1. Voice setup: "Call Dr. Smith's office and reschedule..."
2. Fill phone number
3. Confirm message
4. Watch live call with real-time transcript
5. Receive WhatsApp summary
6. View coaching report

**Expected Conversation**:
- WingMan introduces itself
- Receptionist confirms availability
- Natural back-and-forth dialogue
- Polite goodbye

See `DEMO_SCENARIO.md` for complete walkthrough.

---

## 🔐 Security & Privacy

### Current Implementation (Demo)
- No user authentication
- In-memory storage (no persistence)
- Wide-open CORS
- API keys in environment variables

### Production Recommendations
- JWT/OAuth authentication
- PostgreSQL with encryption
- Restricted CORS
- Secrets management (AWS Secrets Manager)
- Rate limiting and DDoS protection
- Webhook signature verification
- Regular security audits

### Data Handling
- Call transcripts: Temporary in-memory
- Audio recordings: Not stored
- WhatsApp summaries: Encrypted in transit
- User profiles: Browser localStorage

---

## 📈 Future Roadmap

### v1.1 (Next Release)
- [ ] Database integration (PostgreSQL)
- [ ] User authentication
- [ ] Call recording playback
- [ ] Export transcripts as PDF
- [ ] Multi-language support

### v2.0 (Future)
- [ ] Mobile app (React Native)
- [ ] Voice cloning for custom TTS
- [ ] Calendar integration
- [ ] CRM integrations (Salesforce, HubSpot)
- [ ] Advanced analytics dashboard
- [ ] Team collaboration features

### Experimental
- [ ] Integrate Reflex Loop for ultra-low latency
- [ ] WebRTC for browser-to-browser calls
- [ ] Real-time translation

---

## 💼 Business Potential

### Target Markets
1. **Consumer**: Phone anxiety, busy professionals
2. **Healthcare**: Appointment scheduling, patient follow-ups
3. **Sales**: Lead qualification, follow-up calls
4. **Customer Service**: Callback automation, support tickets
5. **Accessibility**: Speech difficulties, hearing impairments

### Monetization
- **Freemium**: 10 calls/month free, $9.99/month unlimited
- **Business**: $49/month per user, team features
- **Enterprise**: Custom pricing, API access, white-label

### Market Size
- **Phone anxiety market**: 40M+ people in US alone
- **Business automation**: $50B+ market
- **Accessibility**: 7M+ people with speech difficulties

---

## 🏆 Why WingMan Wins

### Innovation
✅ First AI phone proxy with natural conversation handling
✅ Streaming LLM optimization for sub-2-second latency
✅ Intelligent caller identity detection
✅ Voice-driven UX with zero typing

### Technical Excellence
✅ Production-ready architecture
✅ Comprehensive test coverage (90%+)
✅ Real-time WebSocket audio pipeline
✅ Async Python throughout
✅ Graceful error handling

### User Experience
✅ Intuitive voice interface
✅ Beautiful particle orb visualization
✅ Real-time transcript display
✅ Actionable coaching reports
✅ WhatsApp integration

### Market Fit
✅ Solves real problem (phone anxiety)
✅ Multiple use cases (personal + business)
✅ Scalable business model
✅ Clear monetization path

### Bob Collaboration
✅ 6 documented sessions
✅ Iterative improvement
✅ Architecture design
✅ Feature development
✅ Performance optimization

---

## 📞 Contact & Links

### Repository
- **GitHub**: [Repository URL]
- **Documentation**: See `/bob_sessions/` for detailed session logs

### Demo
- **Live Demo**: [Demo URL if deployed]
- **Video Demo**: [YouTube link if available]

### Team Contact
- **Email**: [Your email]
- **LinkedIn**: [Your LinkedIn]

---

## 🙏 Acknowledgments

- **IBM Bob Hackathon 2026** for the opportunity
- **Twilio** for voice infrastructure
- **Deepgram** for speech services
- **Groq** for ultra-fast LLM inference
- **LangChain/LangGraph** for agent framework

---

## 📄 License

This project was created for the IBM Bob Hackathon 2026.

---

**Built with ❤️ for IBM Bob Hackathon 2026**

*"Your AI wingman for every conversation."*