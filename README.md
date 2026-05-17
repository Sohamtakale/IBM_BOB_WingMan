# 🪽 WingMan - Your AI Phone Proxy

> **"I handle the conversations you don't want to have."**

WingMan is an AI-powered phone assistant that makes calls on your behalf, provides real-time conversation coaching, and analyzes your performance. Built for the IBM Bob Hackathon 2026.

![WingMan Dashboard](frontend/public/wingman2.png)

## ✨ Features

### 🤖 AutoPilot Mode
WingMan makes the entire call for you:
- Voice-driven call setup using Web Speech API
- AI conducts natural conversations with recipients
- Real-time transcript display
- Automatic WhatsApp summary after call
- Post-call coaching report

**Use Cases**: 
- "Call my landlord and tell them the rent will be 2 days late"
- "Call the restaurant and make a reservation for 4 people at 7 PM"
- "Call my professor and ask about the assignment deadline"

### 🎧 Co-Pilot Mode
Real-time suggestions during YOUR calls:
- Listens to your conversation via microphone
- Provides 3 response options in different tones (Confident, Diplomatic, Detailed)
- Floating popup window overlays on video calls
- Intent classification (question, objection, small talk, etc.)

**Use Cases**:
- Job interviews
- Salary negotiations
- Difficult conversations
- Sales calls

### 📊 Performance Coach
Post-call analysis and feedback:
- Confidence score (0-100)
- Goal achievement tracking
- What went well / What to improve
- Actionable improvement tips
- Full transcript review

## 🏗️ Architecture

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
                    EXTERNAL SERVICES                     │
└───────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Chrome/Edge browser** (for Web Speech API)
- **API Keys**:
  - [Twilio](https://www.twilio.com/) (Account SID, Auth Token, Phone Number)
  - [Deepgram](https://deepgram.com/) (API Key)
  - [Groq](https://groq.com/) (API Key)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd wingman
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

   Required variables:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   DEEPGRAM_API_KEY=your_deepgram_key
   GROQ_API_KEY=your_groq_key
   BASE_URL=http://localhost:8000
   ```

3. **Install backend dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**:
   ```bash
   cd ../frontend
   npm install
   ```

5. **Run the application**:

   **Option A: Using the start script** (recommended):
   ```bash
   cd ..
   chmod +x start.sh
   ./start.sh
   ```

   **Option B: Manual start**:
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

6. **Access the app**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### First-Time Setup

1. Open http://localhost:5173
2. Complete the onboarding form with your details
3. You'll be redirected to the Dashboard
4. Choose a mode and start!

## 📖 Usage Guide

### Making Your First AutoPilot Call

1. **Navigate to AutoPilot** from Dashboard
2. **Voice Setup**:
   - WingMan asks: "Who do you want to call?"
   - Say the name (e.g., "Mom")
   - Fill in phone number when prompted
   - Say your message when asked
3. **Review & Edit**: Check the message, edit if needed
4. **Call**: Click "📞 Call now"
5. **Watch Live**: See the conversation unfold in real-time
6. **Get Debrief**: View coaching report after call ends

**Demo Note**: Twilio trial accounts can only call verified numbers. Use `+917058809304` or `+919579560024` for testing.

### Using Co-Pilot During a Call

1. **Navigate to Co-Pilot** from Dashboard
2. **Set Context**:
   - Who you're talking to
   - Your goal for the conversation
   - Your preferred tone
3. **Start Listening**: Click "I'm ready. Let's go."
4. **Pop Out**: Click "⧉ Pop Out" to open floating window
5. **Position**: Drag the popup over your video call
6. **Talk**: As you speak, WingMan listens and suggests responses
7. **Pick**: Choose from 3 suggestions (Confident, Diplomatic, Detailed)

### Reviewing Coach Reports

1. **From Dashboard**: Click any completed call
2. **View Metrics**:
   - Confidence score
   - Goal achievement
   - Summary
3. **Read Feedback**:
   - What you crushed
   - Real talk (areas to improve)
   - Next time tips
4. **Review Transcript**: See the full conversation

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Twilio**: Phone call infrastructure
- **Deepgram**: Speech-to-Text (Nova-2) & Text-to-Speech (Aura)
- **Groq**: Ultra-fast LLM inference (Llama 3.1 8B Instant)
- **LangGraph**: Agent orchestration framework
- **WebSockets**: Real-time bidirectional communication

### Frontend
- **React 18**: UI library
- **Vite**: Build tool and dev server
- **React Router**: Client-side routing
- **Web Speech API**: Browser speech recognition/synthesis
- **Tailwind CSS**: Utility-first styling

### Key Libraries
```
Backend:
- fastapi==0.115.12
- twilio==9.6.4
- deepgram-sdk==3.7.1
- groq==1.0.0
- langgraph==0.2.74

Frontend:
- react==18.3.1
- react-router-dom==6.30.0
- vite==6.3.5
```

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
│   └── agents/
│       └── pipeline.py      # LangGraph agent (intent + generation)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Router setup
│   │   ├── main.jsx         # Entry point
│   │   ├── index.css        # Global styles
│   │   └── components/
│   │       ├── Dashboard.jsx    # Home screen
│   │       ├── AutoPilot.jsx    # AI calling interface
│   │       ├── CoPilot.jsx      # Live call assistant
│   │       ├── CoachReport.jsx  # Performance analysis
│   │       └── Onboarding.jsx   # User setup
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
├── reflex-loop/             # Experimental low-latency voice agent
├── .env.example             # Environment variables template
├── start.sh                 # Startup script
├── ARCHITECTURE.md          # System design documentation
├── DATA_FLOW.md             # Detailed data flow diagrams
├── CONTRIBUTING.md          # Contribution guidelines
└── README.md                # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | Yes | - |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | Yes | - |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number | Yes | - |
| `DEEPGRAM_API_KEY` | Deepgram API key | Yes | - |
| `GROQ_API_KEY` | Groq API key | Yes | - |
| `BASE_URL` | Backend URL (must be public for Twilio) | Yes | `http://localhost:8000` |
| `WHATSAPP_FROM` | Twilio WhatsApp sender | No | `whatsapp:+14155238886` |
| `WHATSAPP_TO` | Your WhatsApp number | No | - |

### Twilio Setup

1. **Sign up** at [twilio.com](https://www.twilio.com/)
2. **Get a phone number** with Voice capabilities
3. **Copy credentials** from Console Dashboard
4. **Verify numbers** you want to call (trial account limitation)
5. **Set webhook URL** (use ngrok for local development):
   ```bash
   ngrok http 8000
   # Use the https URL as BASE_URL
   ```

### Deepgram Setup

1. **Sign up** at [deepgram.com](https://deepgram.com/)
2. **Create API key** from Console
3. **Copy key** to `.env`

### Groq Setup

1. **Sign up** at [console.groq.com](https://console.groq.com/)
2. **Create API key**
3. **Copy key** to `.env`

## 🐛 Troubleshooting

### Common Issues

**"Popup blocked" in Co-Pilot**
- Allow popups for `localhost:5173` in browser settings
- Chrome: Settings → Privacy and security → Site Settings → Pop-ups and redirects

**"Web Speech API not supported"**
- Use Chrome or Edge (Safari/Firefox not fully supported)
- Ensure microphone permissions are granted

**Twilio call fails immediately**
- Check phone number is verified in Twilio console (trial accounts)
- Ensure `BASE_URL` is publicly accessible (use ngrok for local dev)
- Verify webhook URL format: `https://your-domain.com/twilio/voice/{call_id}`

**No audio during call**
- Check Deepgram API key is valid and has credits
- Verify stable internet connection
- Look for errors in backend terminal

**Backend crashes on call**
- Ensure all environment variables are set correctly
- Check API rate limits (Groq free tier: 30 requests/minute)
- Review backend logs for specific errors

**Frontend shows "Backend not running"**
- Verify backend is running on port 8000
- Check CORS settings in `main.py`
- Ensure no firewall blocking localhost connections

### Debug Mode

Enable detailed logging:

```python
# backend/main.py
logging.basicConfig(level=logging.DEBUG)
```

Check logs:
```bash
# Backend logs
tail -f backend.log

# Frontend console
# Open browser DevTools (F12) → Console tab
```

## 📊 Performance

### Latency Metrics

- **Response Time**: ~1-2 seconds (caller finishes speaking → hears WingMan)
- **Breakdown**:
  - Deepgram STT: ~200-400ms
  - Groq LLM: ~500-1000ms
  - Deepgram TTS: ~300-600ms
  - Network overhead: ~200ms

### Scalability

**Current Limitations**:
- In-memory storage (single instance only)
- No database persistence
- Synchronous call processing

**Production Recommendations**:
- PostgreSQL for persistent storage
- Redis for caching and sessions
- Message queue (RabbitMQ/Celery) for async processing
- Load balancer for multiple instances
- CDN for static assets

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick Start**:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test thoroughly
5. Commit: `git commit -m "Add: amazing feature"`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Complete system architecture overview
- **[DATA_FLOW.md](DATA_FLOW.md)**: Detailed data flow diagrams
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Contribution guidelines for developers

## 🔐 Security & Privacy

**Current Status** (Hackathon Demo):
- No user authentication
- In-memory storage (no persistence)
- Wide-open CORS
- API keys in environment variables

**Production Recommendations**:
- Implement JWT/OAuth authentication
- Encrypt sensitive data at rest and in transit
- Restrict CORS to specific origins
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Add rate limiting and DDoS protection
- Implement webhook signature verification
- Regular security audits

**Data Handling**:
- Call transcripts stored temporarily in memory
- No audio recordings saved (unless explicitly implemented)
- WhatsApp summaries sent via Twilio (encrypted in transit)
- User profiles stored in browser localStorage

## 📄 License

This project was created for the IBM Bob Hackathon 2026.

## 🙏 Acknowledgments

- **IBM Bob Hackathon 2026** for the opportunity
- **Twilio** for voice infrastructure
- **Deepgram** for speech services
- **Groq** for ultra-fast LLM inference
- **LangChain/LangGraph** for agent framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: your-email@example.com

## 🗺️ Roadmap

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

**Built with ❤️ for IBM Bob Hackathon 2026**

*"Your AI wingman for every conversation."*
