# WingMan Architecture Overview

## System Architecture

WingMan is an AI-powered phone proxy system that makes calls on behalf of users. The system consists of three main components:

### 1. **Backend (FastAPI)**
- **Location**: `/backend`
- **Framework**: FastAPI with Python
- **Purpose**: Orchestrates calls, manages state, integrates with external services

### 2. **Frontend (React)**
- **Location**: `/frontend`
- **Framework**: React with Vite
- **Purpose**: User interface for three modes: AutoPilot, Co-Pilot, and Coach

### 3. **Reflex Loop (Optional)**
- **Location**: `/reflex-loop`
- **Purpose**: Experimental low-latency voice agent with interrupt capability
- **Status**: Standalone component, not integrated with main app

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  AutoPilot   │  │   Co-Pilot   │  │    Coach     │          │
│  │  (AI Calls)  │  │ (Live Hints) │  │  (Reports)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                  │
│                            │                                      │
│                    HTTP/WebSocket                                │
└────────────────────────────┼──────────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────┐
│                    BACKEND (FastAPI)                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    main.py (API Routes)                   │   │
│  │  /profile  /autopilot/start  /calls  /copilot/suggest    │   │
│  └────┬─────────────┬──────────────┬────────────────┬───────┘   │
│       │             │              │                │             │
│  ┌────▼─────┐  ┌───▼──────┐  ┌───▼────────┐  ┌───▼──────┐     │
│  │ storage  │  │  twilio  │  │   copilot  │  │  coach   │     │
│  │  (RAM)   │  │ _handler │  │  (agents)  │  │ (report) │     │
│  └──────────┘  └────┬─────┘  └─────┬──────┘  └────┬─────┘     │
│                     │               │              │             │
└─────────────────────┼───────────────┼──────────────┼─────────────┘
                      │               │              │
        ┌─────────────┼───────────────┼──────────────┼─────────────┐
        │             │               │              │             │
   ┌────▼────┐   ┌───▼────┐    ┌────▼─────┐   ┌───▼────┐        │
   │ Twilio  │   │Deepgram│    │  Groq    │   │ Groq   │        │
   │  Voice  │   │  STT   │    │   LLM    │   │  LLM   │        │
   │   API   │   │  TTS   │    │(LangGraph)│   │(Coach) │        │
   └─────────┘   └────────┘    └──────────┘   └────────┘        │
                                                                   │
                        EXTERNAL SERVICES                         │
                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### Backend Components

#### 1. **main.py** - API Server
- FastAPI application with CORS middleware
- Routes for profile management, call control, and AI features
- Integrates all backend modules

#### 2. **twilio_handler.py** - Call Orchestration
- **WebSocket Handler**: Manages real-time audio streaming from Twilio
- **Voice Webhook**: TwiML generation for call setup
- **Audio Pipeline**: 
  - Receives μ-law audio from Twilio
  - Sends to Deepgram for transcription
  - Processes with Groq LLM
  - Generates TTS with Deepgram
  - Streams back to Twilio
- **WhatsApp Integration**: Sends call summaries via WhatsApp

#### 3. **storage.py** - In-Memory State
- Stores call records, transcripts, and user profiles
- Simple dictionary-based storage (not persistent)
- Manages call lifecycle states

#### 4. **coach.py** - Post-Call Analysis
- Generates coaching reports using Groq LLM
- Analyzes conversation quality, goal achievement
- Provides actionable feedback

#### 5. **copilot.py** - Real-Time Suggestions
- Uses LangGraph agent pipeline
- Classifies user intent
- Generates 3 response suggestions with different tones

#### 6. **agents/pipeline.py** - LangGraph Agent
- Two-node graph: Classifier → Generator
- Intent classification: question, objection, small_talk, IVR, trap, statement
- Multi-tone response generation

#### 7. **models.py** - Data Models
- Pydantic models for type safety
- Defines: UserProfile, CallBrief, CallRecord, CoachReport, etc.

### Frontend Components

#### 1. **App.jsx** - Router
- React Router setup
- Profile-based route protection
- Navigation between modes

#### 2. **Dashboard.jsx** - Home Screen
- Call history display
- Performance metrics
- Module cards for AutoPilot, Co-Pilot, Coach

#### 3. **AutoPilot.jsx** - AI Calling Interface
- Voice-driven call setup using Web Speech API
- Particle orb visualization with dynamic states
- Live transcript display during calls
- Real-time call status polling

#### 4. **CoPilot.jsx** - Live Call Assistant
- Continuous speech recognition
- Floating popup window for overlay on video calls
- Real-time suggestion generation
- Intent detection display

#### 5. **CoachReport.jsx** - Performance Analysis
- Score visualization with SVG rings
- Strengths and weaknesses breakdown
- Actionable improvement tips
- Full transcript review

#### 6. **Onboarding.jsx** - User Setup
- Profile creation form
- Stores user preferences for AI personalization

---

## Data Models

### CallRecord
```python
{
  "call_id": str,
  "phone_number": str,
  "call_brief": CallBrief,
  "user_profile": UserProfile,
  "status": CallStatus,  # initiating, in_progress, completed, failed
  "transcript": List[TranscriptTurn],
  "twilio_call_sid": str,
  "coach_report": CoachReport
}
```

### CallBrief
```python
{
  "who_calling": str,
  "goal": str,
  "key_points": str,
  "questions_to_ask": str,
  "things_to_avoid": str,
  "tone": str
}
```

### CoachReport
```python
{
  "confidence_score": int,  # 0-100
  "goal_achieved": bool,
  "goal_achievement_score": int,
  "what_went_well": List[str],
  "what_to_improve": List[str],
  "improvements": List[str],
  "summary": str
}
```

---

## Technology Stack

### Backend
- **FastAPI**: Web framework
- **Twilio**: Phone call infrastructure
- **Deepgram**: Speech-to-Text (Nova-2) and Text-to-Speech (Aura)
- **Groq**: LLM inference (Llama 3.1 8B Instant)
- **LangGraph**: Agent orchestration framework
- **WebSockets**: Real-time audio streaming
- **httpx**: Async HTTP client

### Frontend
- **React 18**: UI framework
- **React Router**: Navigation
- **Vite**: Build tool
- **Web Speech API**: Browser-based speech recognition/synthesis
- **Tailwind CSS**: Styling (via index.css)

### External Services
- **Twilio Voice API**: Phone call handling
- **Twilio WhatsApp**: Post-call summaries
- **Deepgram API**: STT/TTS
- **Groq API**: LLM inference

---

## State Management

### Call States
1. **INITIATING**: Call request sent to Twilio
2. **IN_PROGRESS**: WebSocket connected, conversation active
3. **COMPLETING**: Goodbye detected, wrapping up
4. **COMPLETED**: Call ended, coach report generated
5. **FAILED**: Error occurred

### Storage Strategy
- **In-Memory**: All data stored in Python dictionaries
- **No Persistence**: Data lost on server restart
- **Frontend Cache**: User profile stored in localStorage

---

## Security Considerations

### Current Implementation
- **CORS**: Wide open (`allow_origins=["*"]`)
- **No Authentication**: All endpoints publicly accessible
- **API Keys**: Stored in environment variables
- **Local Storage**: Profile data in browser

### Production Recommendations
- Implement user authentication (JWT/OAuth)
- Restrict CORS to specific origins
- Add rate limiting
- Use database for persistent storage
- Encrypt sensitive data
- Implement webhook signature verification for Twilio

---

## Scalability Considerations

### Current Limitations
- In-memory storage (single instance only)
- No load balancing support
- Synchronous call processing
- No queue system

### Scaling Path
1. **Database**: Replace storage.py with PostgreSQL/MongoDB
2. **Redis**: Cache and session management
3. **Message Queue**: RabbitMQ/Celery for async processing
4. **Load Balancer**: Multiple backend instances
5. **CDN**: Static frontend assets
6. **Monitoring**: Logging, metrics, error tracking

---

## Development Workflow

### Backend Development
```bash
cd wingman/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd wingman/frontend
npm install
npm run dev
```

### Environment Variables Required
```
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
DEEPGRAM_API_KEY=
GROQ_API_KEY=
BASE_URL=https://your-domain.com
WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+91XXXXXXXXXX
```

---

## Future Enhancements

1. **Persistent Storage**: Database integration
2. **User Accounts**: Multi-user support with authentication
3. **Call Recording**: Audio file storage and playback
4. **Advanced Analytics**: Trend analysis, performance tracking
5. **Multi-Language**: Support for languages beyond English
6. **Voice Cloning**: Custom TTS voices
7. **Calendar Integration**: Automated scheduling
8. **CRM Integration**: Sync with Salesforce, HubSpot
9. **Mobile App**: Native iOS/Android apps
10. **Reflex Loop Integration**: Ultra-low latency voice mode