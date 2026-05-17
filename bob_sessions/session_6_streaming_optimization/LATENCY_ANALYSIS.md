# WingMan Call Pipeline Latency Analysis & Streaming Optimization

## Current Pipeline Analysis

### Sequential Pipeline (2-4 seconds per turn)

```
┌─────────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐
│   Twilio    │───▶│ Deepgram │───▶│   Groq   │───▶│  Deepgram   │───▶ Twilio
│   Audio     │    │   STT    │    │   LLM    │    │    TTS      │    WebSocket
└─────────────┘    └──────────┘    └──────────┘    └─────────────┘
  Real-time         ~500-800ms      ~800-1500ms      ~600-1200ms
```

### Latency Breakdown

1. **Deepgram STT (500-800ms)**
   - Real-time streaming with `utterance_end_ms=2500`
   - Waits for speech pause before finalizing
   - **Contribution: ~20-25% of total latency**
   - Already optimized with streaming

2. **Groq LLM (800-1500ms)** ⚠️ **MAJOR BOTTLENECK**
   - Currently using `stream=False` (line 356)
   - Waits for complete response before proceeding
   - Model: `llama-3.1-8b-instant`
   - **Contribution: ~35-40% of total latency**
   - **OPTIMIZATION TARGET #1**

3. **Deepgram TTS (600-1200ms)** ⚠️ **MAJOR BOTTLENECK**
   - Generates entire audio file before sending
   - Single API call for full text (line 215-226)
   - **Contribution: ~30-35% of total latency**
   - **OPTIMIZATION TARGET #2**

4. **Twilio WebSocket Transmission (100-200ms)**
   - Already chunked (160-byte chunks, line 387-393)
   - **Contribution: ~5-10% of total latency**
   - Already optimized

### Key Findings

**The main latency contributors are:**
1. **LLM waiting for complete response** (800-1500ms)
2. **TTS waiting for complete audio generation** (600-1200ms)
3. **Sequential processing** - TTS can't start until LLM finishes

**Total avoidable latency: 1400-2700ms (70-90% of current latency)**

## Streaming Architecture Design

### Proposed Pipeline

```
┌─────────────┐    ┌──────────┐    ┌──────────────────────────────┐
│   Twilio    │───▶│ Deepgram │───▶│   Groq LLM (streaming)       │
│   Audio     │    │   STT    │    │   ↓ token by token           │
└─────────────┘    └──────────┘    │   ↓ sentence buffering       │
                                    │   ↓ emit complete sentences  │
                                    └──────────┬───────────────────┘
                                               ↓
                                    ┌──────────▼───────────────────┐
                                    │  Deepgram TTS (per sentence) │
                                    │  ↓ parallel requests         │
                                    │  ↓ stream audio chunks       │
                                    └──────────┬───────────────────┘
                                               ↓
                                    ┌──────────▼───────────────────┐
                                    │  Twilio WebSocket            │
                                    │  (chunked transmission)      │
                                    └──────────────────────────────┘
```

### Key Improvements

1. **Streaming LLM Response**
   - Enable `stream=True` in Groq API
   - Buffer tokens into complete sentences
   - Emit sentences as soon as they're complete
   - **Reduces perceived latency by 60-80%**

2. **Parallel TTS Processing**
   - Generate TTS for each sentence independently
   - Start TTS as soon as first sentence is ready
   - Pipeline multiple TTS requests
   - **Reduces TTS wait time by 70-90%**

3. **Sentence-Level Streaming**
   - Split on `.`, `!`, `?` with proper handling
   - Minimum sentence length to avoid fragmentation
   - Preserve natural speech rhythm

### Expected Performance

**Current:** 2000-4000ms total latency
**Optimized:** 600-1200ms time-to-first-audio

**Breakdown:**
- STT: 500-800ms (unchanged)
- LLM first sentence: 200-400ms (vs 800-1500ms)
- TTS first chunk: 150-300ms (vs 600-1200ms)
- **Total: 850-1500ms** (57-62% reduction)

**Subsequent sentences:** Near-zero additional latency (pipelined)

## Implementation Strategy

### 1. Streaming LLM Handler

```python
async def stream_llm_response(messages, sentence_queue):
    """Stream LLM response and emit complete sentences"""
    buffer = ""
    async for chunk in groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        stream=True,
        temperature=0.6,
        max_tokens=150,
    ):
        if chunk.choices[0].delta.content:
            buffer += chunk.choices[0].delta.content
            
            # Check for sentence boundaries
            sentences = split_into_sentences(buffer)
            for sentence in sentences[:-1]:  # Keep last partial
                await sentence_queue.put(sentence)
            buffer = sentences[-1] if sentences else ""
    
    # Emit remaining buffer
    if buffer.strip():
        await sentence_queue.put(buffer.strip())
```

### 2. Parallel TTS Processing

```python
async def tts_loop():
    """Process TTS requests in parallel with streaming"""
    while True:
        sentence = await sentence_queue.get()
        
        # Generate TTS for this sentence
        asyncio.create_task(
            generate_and_send_tts(sentence, stream_sid, websocket)
        )
```

### 3. Sentence Splitting Logic

```python
def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving incomplete ones"""
    # Handle common sentence endings
    pattern = r'([.!?]+[\s\n]+)'
    parts = re.split(pattern, text)
    
    sentences = []
    current = ""
    for part in parts:
        current += part
        if re.match(pattern, part):
            if len(current.strip()) >= 10:  # Minimum length
                sentences.append(current.strip())
                current = ""
    
    # Add remaining text as incomplete sentence
    if current:
        sentences.append(current)
    
    return sentences
```

## Risk Mitigation

### Potential Issues

1. **Sentence fragmentation**
   - Risk: Breaking mid-sentence creates unnatural pauses
   - Mitigation: Minimum sentence length, smart boundary detection

2. **TTS request ordering**
   - Risk: Audio chunks arrive out of order
   - Mitigation: Sequence numbers, ordered queue

3. **Error handling**
   - Risk: Failed TTS for one sentence blocks pipeline
   - Mitigation: Independent error handling per sentence

4. **Memory usage**
   - Risk: Multiple parallel TTS requests
   - Mitigation: Limit concurrent TTS requests (max 3)

### Fallback Strategy

If streaming fails:
1. Catch exceptions in streaming code
2. Fall back to current non-streaming approach
3. Log error for monitoring
4. Continue call without interruption

## Testing Strategy

1. **Unit tests**: Sentence splitting logic
2. **Integration tests**: Streaming pipeline end-to-end
3. **Load tests**: Multiple concurrent calls
4. **Latency measurement**: Before/after comparison
5. **Quality tests**: Audio quality, naturalness

## Monitoring Metrics

Track these metrics:
- Time to first audio (TTFA)
- Total response latency
- Sentence processing time
- TTS generation time per sentence
- Error rates for streaming vs non-streaming