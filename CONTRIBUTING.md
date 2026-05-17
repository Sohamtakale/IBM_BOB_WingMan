# Contributing to WingMan

Welcome! This guide will help you understand the WingMan codebase and start contributing.

## 🎯 Project Overview

WingMan is an AI phone proxy that makes calls on behalf of users. It has three main modes:

1. **AutoPilot**: AI makes the entire call autonomously
2. **Co-Pilot**: Real-time suggestions during your own calls
3. **Coach**: Post-call performance analysis

## 🏗️ Architecture

```
wingman/
├── backend/          # FastAPI server
│   ├── main.py              # API routes
│   ├── twilio_handler.py    # Call orchestration
│   ├── storage.py           # In-memory data store
│   ├── coach.py             # Post-call analysis
│   ├── copilot.py           # Real-time suggestions
│   ├── models.py            # Pydantic data models
│   └── agents/
│       └── pipeline.py      # LangGraph agent
├── frontend/         # React UI
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── Dashboard.jsx
│           ├── AutoPilot.jsx
│           ├── CoPilot.jsx
│           ├── CoachReport.jsx
│           └── Onboarding.jsx
└── reflex-loop/      # Experimental low-latency voice agent
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **API Keys**:
  - Twilio (Account SID, Auth Token, Phone Number)
  - Deepgram (for STT/TTS)
  - Groq (for LLM)

### Setup

1. **Clone and navigate**:
   ```bash
   cd wingman
   ```

2. **Backend setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   cp ../.env.example .env
   # Edit .env with your API keys
   ```

3. **Frontend setup**:
   ```bash
   cd ../frontend
   npm install
   ```

4. **Run both**:
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn main:app --reload

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

5. **Access**: Open http://localhost:5173

### Environment Variables

Create `.env` in the project root:

```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Deepgram
DEEPGRAM_API_KEY=your_deepgram_key

# Groq
GROQ_API_KEY=your_groq_key

# Server
BASE_URL=http://localhost:8000

# WhatsApp (optional)
WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+91XXXXXXXXXX
```

## 📚 Key Concepts

### Call Lifecycle

1. **INITIATING**: User submits call request
2. **IN_PROGRESS**: WebSocket connected, conversation active
3. **COMPLETING**: Goodbye detected, wrapping up
4. **COMPLETED**: Call ended, coach report generated
5. **FAILED**: Error occurred

### Data Flow

```
User → Frontend → Backend → Twilio → Phone Network
                     ↓
                 Deepgram STT → Groq LLM → Deepgram TTS
                     ↓
                 Storage (in-memory)
```

### Storage

Currently uses in-memory dictionaries (`storage.py`). Data is lost on restart. This is intentional for the hackathon demo but should be replaced with a database for production.

## 🛠️ Development Guidelines

### Code Style

**Backend (Python)**:
- Follow PEP 8
- Use type hints
- Async/await for I/O operations
- Pydantic models for data validation

**Frontend (React)**:
- Functional components with hooks
- Inline styles (no CSS modules currently)
- Descriptive variable names
- Comments for complex logic

### Adding a New Feature

#### Backend Example: Add a new API endpoint

1. **Define model** in `models.py`:
   ```python
   class NewFeatureRequest(BaseModel):
       param1: str
       param2: int
   ```

2. **Add route** in `main.py`:
   ```python
   @app.post("/new-feature")
   async def new_feature(request: NewFeatureRequest):
       # Your logic here
       return {"result": "success"}
   ```

3. **Update storage** if needed in `storage.py`:
   ```python
   def save_new_data(data):
       _new_data_store[data.id] = data
   ```

#### Frontend Example: Add a new component

1. **Create component** in `src/components/NewFeature.jsx`:
   ```jsx
   import { useState } from 'react'
   import { useNavigate } from 'react-router-dom'

   export default function NewFeature() {
     const navigate = useNavigate()
     const [data, setData] = useState(null)

     return (
       <div>
         {/* Your UI */}
       </div>
     )
   }
   ```

2. **Add route** in `App.jsx`:
   ```jsx
   <Route path="/new-feature" element={<NewFeature />} />
   ```

3. **Add navigation** in `Dashboard.jsx`:
   ```jsx
   <button onClick={() => navigate('/new-feature')}>
     New Feature
   </button>
   ```

### Testing

Currently no automated tests. Manual testing workflow:

1. **Backend**: Use curl or Postman
   ```bash
   curl -X POST http://localhost:8000/profile \
     -H "Content-Type: application/json" \
     -d '{"name":"Test User"}'
   ```

2. **Frontend**: Use browser DevTools
   - Check Console for errors
   - Monitor Network tab for API calls
   - Test on Chrome (Web Speech API required)

3. **End-to-End**: Make a test call
   - Use verified Twilio numbers only (trial account)
   - Check transcript updates in real-time
   - Verify coach report generation

## 🐛 Common Issues

### "Popup blocked" in Co-Pilot
- **Solution**: Allow popups for localhost:5173 in browser settings

### "Web Speech API not supported"
- **Solution**: Use Chrome or Edge (Safari/Firefox not supported)

### Twilio call fails
- **Solution**: 
  - Check phone number is verified in Twilio console
  - Ensure BASE_URL is publicly accessible (use ngrok for local dev)
  - Verify webhook URL is correct

### Audio quality issues
- **Solution**:
  - Check Deepgram API key is valid
  - Ensure stable internet connection
  - Try different TTS voice in `twilio_handler.py`

### Backend crashes on call
- **Solution**:
  - Check all environment variables are set
  - Look for errors in terminal
  - Verify API rate limits not exceeded

## 🎨 UI/UX Guidelines

### Design System

- **Colors**:
  - Background: `#000` (black)
  - Cards: `#0e0e0e` with `#1e1e1e` border
  - Text: `#fff` (primary), `#555` (secondary), `#333` (tertiary)
  - Success: `#4ade80` (green)
  - Error: `#f87171` (red)
  - Accent: `#22d3ee` (cyan)

- **Typography**:
  - Font: System font stack (Inter-like)
  - Headings: 700-900 weight
  - Body: 400-600 weight

- **Spacing**:
  - Use multiples of 4px (4, 8, 12, 16, 20, 24, 32, 48)

- **Animations**:
  - Keep subtle (0.15-0.2s transitions)
  - Use for hover states and loading indicators

### Component Patterns

**Button**:
```jsx
<button style={{
  background: '#fff',
  color: '#000',
  border: 'none',
  borderRadius: '8px',
  padding: '12px 20px',
  fontSize: '14px',
  fontWeight: 700,
  cursor: 'pointer'
}}>
  Click me
</button>
```

**Card**:
```jsx
<div style={{
  background: '#0e0e0e',
  border: '1px solid #1e1e1e',
  borderRadius: '12px',
  padding: '20px'
}}>
  Content
</div>
```

**Input**:
```jsx
<input style={{
  width: '100%',
  background: '#0e0e0e',
  border: '1px solid #1e1e1e',
  borderRadius: '8px',
  padding: '12px',
  color: '#fff',
  fontSize: '14px'
}} />
```

## 🔧 Advanced Topics

### Adding a New LLM Provider

1. **Create client** in `backend/llm/`:
   ```python
   class NewLLMClient:
       async def generate(self, messages):
           # API call
           return response
   ```

2. **Update config** to switch providers:
   ```python
   LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
   ```

3. **Modify calls** in `twilio_handler.py` and `coach.py`

### Adding Database Support

1. **Install SQLAlchemy**:
   ```bash
   pip install sqlalchemy asyncpg
   ```

2. **Create models** in `backend/db/models.py`:
   ```python
   from sqlalchemy import Column, String, DateTime
   from sqlalchemy.ext.declarative import declarative_base

   Base = declarative_base()

   class Call(Base):
       __tablename__ = "calls"
       call_id = Column(String, primary_key=True)
       # ... other fields
   ```

3. **Replace storage.py** functions with DB queries

### Deploying to Production

1. **Backend**:
   - Use Gunicorn/Uvicorn with multiple workers
   - Set up PostgreSQL database
   - Configure Redis for caching
   - Use environment-based config

2. **Frontend**:
   - Build: `npm run build`
   - Serve with Nginx or Vercel
   - Update API URL to production backend

3. **Infrastructure**:
   - Use Docker for containerization
   - Deploy to AWS/GCP/Azure
   - Set up CI/CD pipeline
   - Configure monitoring (Sentry, DataDog)

## 📖 Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Twilio Voice API](https://www.twilio.com/docs/voice)
- [Deepgram API](https://developers.deepgram.com/)
- [Groq API](https://console.groq.com/docs)
- [LangGraph](https://langchain-ai.github.io/langgraph/)

### Related Files
- `ARCHITECTURE.md`: System design overview
- `DATA_FLOW.md`: Detailed data flow diagrams
- `README.md`: Quick start guide

## 🤝 Contribution Workflow

1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/your-feature`
3. **Make changes** and test thoroughly
4. **Commit**: `git commit -m "Add: your feature description"`
5. **Push**: `git push origin feature/your-feature`
6. **Create Pull Request** with description of changes

### PR Guidelines

- **Title**: Clear, descriptive (e.g., "Add: Real-time call analytics")
- **Description**: 
  - What changed
  - Why it changed
  - How to test
  - Screenshots (if UI change)
- **Code Quality**:
  - No console.logs in production code
  - Handle errors gracefully
  - Add comments for complex logic
  - Update documentation if needed

## 💡 Ideas for Contribution

### Easy (Good First Issues)
- [ ] Add loading spinners to buttons
- [ ] Improve error messages
- [ ] Add keyboard shortcuts
- [ ] Create dark/light theme toggle
- [ ] Add call duration display

### Medium
- [ ] Implement call recording playback
- [ ] Add export transcript as PDF
- [ ] Create analytics dashboard
- [ ] Add multi-language support
- [ ] Implement user authentication

### Hard
- [ ] Replace in-memory storage with PostgreSQL
- [ ] Add WebRTC for browser-to-browser calls
- [ ] Implement voice cloning for custom TTS
- [ ] Create mobile app (React Native)
- [ ] Add real-time collaboration features

## 📞 Getting Help

- **Issues**: Check existing issues or create new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact project maintainers

## 📄 License

This project is part of the IBM Bob Hackathon 2026. Check LICENSE file for details.

---

**Happy coding! 🚀**