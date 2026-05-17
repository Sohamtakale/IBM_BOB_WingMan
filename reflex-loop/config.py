# config.py
import os
from dotenv import load_dotenv

load_dotenv()
# --- AUDIO CONFIG ---
SAMPLE_RATE = 16000 # Deepgram Aura Output is usually 24kHz or 48kHz, we might need resampling or player adjustment. 
# actually Aura can output 16khz linear16 using format options.
CHANNELS = 1
FORMAT_WIDTH = 2  # 16-bit
FRAME_DURATION_MS = 30  # 20-30ms for VAD
CHUNK_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples for 30ms

# --- VAD CONFIG (TUNED FOR ENERGY FALLBACK) ---
VAD_MODE = 3  # 0-3, 3 is most aggressive

# Energy Threshold:
# 300 was too low (picked up breaths). 
# 600-1000 is better for "Speech only".
VAD_THRESHOLD_ENERGY = 1000 

# Debounce: 
# Require 3 consecutive frames (approx 90ms) of speech to trigger interrupt.
# This ignores clicks, pops, and short noises.
VAD_CONSECUTIVE_FRAMES = 4

# --- ASR CONFIG ---
ASR_PROVIDER = "deepgram"  # "dummy" or "deepgram"
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")  # expected in environment or .env
SILENCE_WINDOW_MS = 100  # Max silence before finalizing
SPEECH_PAD_MS = 100      # Pad start/end of speech

# --- LLM CONFIG ---
LLM_PROVIDER = "groq" # "dummy", "gemini", "groq"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # expected in environment or .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")      # expected in environment or .env
MAX_TOKENS = 120
TEMPERATURE = 0.6
STREAMING = True

SYSTEM_PROMPT = """You are a helpful, empathetic voice assistant.
Your responses must be short, conversational, and interruptible.
Max 2-3 sentences.
Do not use lists or complex formatting.
Act like a human listener."""

# --- TTS CONFIG ---
TTS_PROVIDER = "deepgram" # "deepgram" or "edge" (edge-tts)
# Deepgram Aura Voices: "aura-asteria-en", "aura-luna-en", "aura-stella-en", "aura-athena-en", "aura-hera-en", "aura-orion-en", "aura-arcas-en", "aura-perseus-en", "aura-angus-en"
TTS_VOICE = "aura-asteria-en" 
TTS_FLUSH_WORDS = 3
TTS_FLUSH_ON_PUNCT = True
PUNCTUATION_STOP = {'.', '?', '!', ','}

# --- REFLEX CONFIG ---
INTERRUPT_TIMEOUT_MS = 100
LATENCY_DEBUG = True
