# Session 6 — Performance Optimization: Streaming Pipeline

## What Bob Did
Redesigned the call audio pipeline from sequential to streaming, cutting response latency by 57–62%.

## Latency Breakdown (Before)
| Step | Time |
|------|------|
| STT (Deepgram) | 500–800ms |
| LLM (Groq, blocking) | 800–1500ms |
| TTS (Deepgram, blocking) | 600–1200ms |
| **Total** | **2000–4000ms** |

## Latency Breakdown (After)
| Step | Time |
|------|------|
| STT | 500–800ms |
| LLM first sentence (streaming) | 200–400ms |
| TTS per sentence (parallel) | 150–300ms |
| **Time to first audio** | **850–1500ms** |

## Key Code Changes in `twilio_handler.py`

### New Functions
- `split_into_sentences()` — splits LLM token stream into complete sentences
- `generate_and_send_tts()` — generates + sends TTS for a single sentence

### Modified Functions
- `process_loop()` — `stream=True` on Groq call; emits sentences to queue as they complete
- `tts_loop()` — processes sentences in parallel with semaphore (max 3 concurrent)

### Architecture
- Replaced `tts_queue` with `sentence_queue` for streaming
- Added `tts_sequence_num` for ordering
- Automatic fallback to non-streaming on error

## Result
57–62% latency reduction. First audio reaches caller in under 1 second from end of their speech.
