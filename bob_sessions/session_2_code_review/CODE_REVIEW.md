# In-Depth Review of `backend/twilio_handler.py`

## 1. LATENCY BOTTLENECKS IN AUDIO PIPELINE

### **CRITICAL: Sequential TTS Processing (Lines 296-320)**
**Problem:** The `tts_loop()` processes TTS requests sequentially with blocking `await generate_tts_audio(text)`. If the LLM generates a response while TTS is still processing/sending the previous audio, the new response waits in queue, adding 1-3 seconds of latency.

**Code:**
```python
async def tts_loop():
    while True:
        text = await tts_queue.get()  # Blocks until item available
        audio_bytes = await generate_tts_audio(text)  # 500-2000ms
        # ... chunking and sending (200-500ms for long audio)
```

**Fix:** Process TTS requests concurrently with a semaphore to limit parallel requests:
```python
async def tts_loop():
    semaphore = asyncio.Semaphore(2)  # Max 2 concurrent TTS requests
    
    async def process_tts(text):
        async with semaphore:
            try:
                audio_bytes = await generate_tts_audio(text)
                logger.info(f"[{call_id}] TTS got {len(audio_bytes)} bytes for: {text[:40]!r}")
                if audio_bytes and stream_sid:
                    if len(audio_bytes) % 2:
                        audio_bytes = audio_bytes[:-1]
                    mulaw_audio = pcm16_to_mulaw(audio_bytes)
                    for i in range(0, len(mulaw_audio), 160):
                        chunk = mulaw_audio[i:i + 160]
                        await websocket.send_text(json.dumps({
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": base64.b64encode(chunk).decode()},
                        }))
                    logger.info(f"[{call_id}] TTS sent {len(mulaw_audio)} mulaw bytes")
            except Exception as e:
                logger.error(f"[{call_id}] TTS error: {e}", exc_info=True)
    
    while True:
        text = await tts_queue.get()
        asyncio.create_task(process_tts(text))
```

### **CRITICAL: LLM Blocking in process_loop (Lines 273-280)**
**Problem:** The LLM call blocks the entire transcript processing loop. If Groq takes 800ms to respond, any interim transcripts arriving during that time pile up in the queue, causing the system to feel unresponsive.

**Code:**
```python
resp = await groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=messages,
    temperature=0.6,
    max_tokens=150,
    stream=False,  # ← Not streaming!
)
```

**Fix:** Use streaming to start TTS generation earlier:
```python
# In process_loop, replace lines 273-294 with:
try:
    stream = await groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.6,
        max_tokens=150,
        stream=True,  # Enable streaming
    )
    
    response_text = ""
    first_chunk = True
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            response_text += content
            
            # Send first sentence immediately for lower latency
            if first_chunk and any(p in response_text for p in ['. ', '! ', '? ']):
                first_sentence = response_text.split('. ')[0] + '.'
                await tts_queue.put(first_sentence)
                first_chunk = False
    
    # Send remaining text if not already sent
    if first_chunk and response_text:
        await tts_queue.put(response_text)
        
except Exception as e:
    logger.error(f"[{call_id}] LLM error: {e}")
    response_text = "I'm sorry, could you repeat that?"
    await tts_queue.put(response_text)
```

### **MODERATE: TTS Timeout Too High (Line 160)**
**Problem:** 30-second timeout on TTS requests is excessive. If Deepgram is slow, the user waits 30 seconds before getting an error.

**Code:**
```python
async with httpx.AsyncClient(timeout=30) as client:
```

**Fix:**
```python
async with httpx.AsyncClient(timeout=5.0) as client:  # 5s is reasonable for TTS
```

---

## 2. EDGE CASES IN WEBSOCKET MEDIA STREAM HANDLING

### **CRITICAL: Race Condition on stream_sid (Lines 298, 330)**
**Problem:** `stream_sid` is set in the main WebSocket loop (line 330) but checked in `tts_loop()` (line 304). If TTS completes before the "start" event arrives, audio is silently dropped.

**Code:**
```python
# Line 304 in tts_loop:
if audio_bytes and stream_sid:  # stream_sid might be None!

# Line 330 in main loop:
if event == "start":
    stream_sid = data["start"]["streamSid"]
```

**Fix:** Wait for stream_sid before processing TTS:
```python
# Add after line 198:
stream_sid_ready = asyncio.Event()

# Modify tts_loop (line 297):
async def tts_loop():
    await stream_sid_ready.wait()  # Wait for stream to be ready
    while True:
        text = await tts_queue.get()
        # ... rest of code

# In main loop after line 331:
if event == "start":
    stream_sid = data["start"]["streamSid"]
    stream_sid_ready.set()  # Signal that stream is ready
    logger.info(f"[{call_id}] Stream started: {stream_sid}")
```

### **CRITICAL: No Handling for Malformed JSON (Line 326)**
**Problem:** `json.loads(raw_msg)` will crash the entire WebSocket handler if Twilio sends malformed JSON, terminating the call.

**Code:**
```python
async for raw_msg in websocket.iter_text():
    data = json.loads(raw_msg)  # Can raise JSONDecodeError
```

**Fix:**
```python
async for raw_msg in websocket.iter_text():
    try:
        data = json.loads(raw_msg)
    except json.JSONDecodeError as e:
        logger.error(f"[{call_id}] Invalid JSON from Twilio: {e}, msg: {raw_msg[:100]}")
        continue  # Skip this message, don't crash
    
    event = data.get("event")
```

### **MODERATE: Missing "mark" Event Handling**
**Problem:** Twilio sends "mark" events to confirm audio playback. Ignoring these means you can't detect if audio is actually playing or if there's a buffer underrun.

**Fix:** Add after line 347:
```python
elif event == "mark":
    mark_name = data.get("mark", {}).get("name")
    logger.debug(f"[{call_id}] Audio mark reached: {mark_name}")
    # Could use this to track audio playback completion
```

### **CRITICAL: No Cleanup if WebSocket Fails Before "start" Event**
**Problem:** If the WebSocket connection fails before receiving the "start" event (line 329), `stream_sid` remains None, but the Deepgram connection and tasks keep running, leaking resources.

**Fix:** Add timeout for start event:
```python
# After line 244 (after dg_connection.start):
start_timeout = 10  # seconds
start_time = asyncio.get_event_loop().time()

# In main loop, before line 325:
try:
    async for raw_msg in websocket.iter_text():
        # Check if we've been waiting too long for start event
        if stream_sid is None and (asyncio.get_event_loop().time() - start_time) > start_timeout:
            logger.error(f"[{call_id}] Timeout waiting for start event")
            break
        
        data = json.loads(raw_msg)
        # ... rest of code
```

---

## 3. DEEPGRAM SDK EVENT CALLBACK SIGNATURE ISSUES

### **CRITICAL: Incorrect Callback Signature (Lines 208, 224)**
**Problem:** The Deepgram SDK v3.x changed callback signatures. The current code uses `(conn, result, **kwargs)` and `(conn, **kwargs)`, but the SDK now passes `(self, result, **kwargs)` and `(self, **kwargs)` respectively. The `conn` parameter is the connection object itself (self), not a separate parameter.

**Current Code:**
```python
def on_transcript(conn, result, **kwargs):  # ← 'conn' is actually 'self'
    try:
        if result.channel and result.channel.alternatives:
            # ...

def on_utterance_end(conn, **kwargs):  # ← 'conn' is actually 'self'
    asyncio.run_coroutine_threadsafe(...)
```

**Fix:** Update signatures to match SDK:
```python
def on_transcript(self, result, **kwargs):
    try:
        if result.channel and result.channel.alternatives:
            text = result.channel.alternatives[0].transcript
            if text:
                asyncio.run_coroutine_threadsafe(
                    transcript_queue.put({
                        "type": "transcript",
                        "text": text,
                        "is_final": result.is_final,
                    }),
                    loop,
                )
    except Exception as e:
        logger.error(f"[{call_id}] Transcript cb error: {e}")

def on_utterance_end(self, **kwargs):
    asyncio.run_coroutine_threadsafe(
        transcript_queue.put({"type": "utterance_end", "text": "", "is_final": True}),
        loop,
    )
```

### **MODERATE: Missing Error Event Handler**
**Problem:** No handler for `LiveTranscriptionEvents.Error`. If Deepgram encounters an error (API quota, network issue), the system silently fails without logging.

**Fix:** Add after line 231:
```python
def on_error(self, error, **kwargs):
    logger.error(f"[{call_id}] Deepgram error: {error}")
    # Optionally: put error in queue to trigger graceful shutdown

dg_connection.on(LiveTranscriptionEvents.Error, on_error)
```

### **MODERATE: No Metadata Event Handler**
**Problem:** Deepgram sends metadata events with useful info (request_id, duration, etc.). Not capturing this makes debugging harder.

**Fix:** Add after error handler:
```python
def on_metadata(self, metadata, **kwargs):
    logger.debug(f"[{call_id}] Deepgram metadata: {metadata}")

dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
```

---

## 4. ADDITIONAL CRITICAL ISSUES

### **CRITICAL: Unhandled Exception in Callbacks Crashes Thread (Lines 221-222)**
**Problem:** If `transcript_queue.put()` raises an exception (e.g., queue is full or closed), the error is logged but the callback continues to fail silently on subsequent calls.

**Fix:** Add more robust error handling:
```python
def on_transcript(self, result, **kwargs):
    try:
        if result.channel and result.channel.alternatives:
            text = result.channel.alternatives[0].transcript
            if text:
                try:
                    asyncio.run_coroutine_threadsafe(
                        transcript_queue.put({
                            "type": "transcript",
                            "text": text,
                            "is_final": result.is_final,
                        }),
                        loop,
                    ).result(timeout=1.0)  # Add timeout to detect queue issues
                except Exception as queue_err:
                    logger.error(f"[{call_id}] Queue error: {queue_err}")
    except Exception as e:
        logger.error(f"[{call_id}] Transcript cb error: {e}", exc_info=True)
```

### **CRITICAL: Memory Leak in conversation_history (Line 271)**
**Problem:** `conversation_history` grows unbounded. On a 30-minute call with 100 turns, this could consume significant memory and slow down LLM calls.

**Code:**
```python
messages = [{"role": "system", "content": system_prompt}] + conversation_history[-12:]
```

**Fix:** Limit the list itself, not just the slice:
```python
conversation_history.append({"role": "user", "content": utterance})
if len(conversation_history) > 24:  # Keep last 24 turns (12 exchanges)
    conversation_history = conversation_history[-24:]
messages = [{"role": "system", "content": system_prompt}] + conversation_history
```

### **MODERATE: No Graceful Shutdown on Task Cancellation (Lines 352-353)**
**Problem:** Tasks are cancelled abruptly without waiting for cleanup. If TTS is mid-send, audio chunks may be lost.

**Fix:**
```python
finally:
    # Signal tasks to stop gracefully
    await tts_queue.put(None)  # Sentinel value
    await transcript_queue.put(None)
    
    # Wait briefly for graceful shutdown
    try:
        await asyncio.wait_for(asyncio.gather(process_task, tts_task, return_exceptions=True), timeout=2.0)
    except asyncio.TimeoutError:
        process_task.cancel()
        tts_task.cancel()
    
    dg_connection.finish()
```

---

## SUMMARY OF FIXES BY PRIORITY

**CRITICAL (Fix Immediately):**
1. Stream LLM responses for 50-70% latency reduction
2. Fix Deepgram callback signatures (will break in SDK updates)
3. Add stream_sid race condition protection
4. Handle malformed JSON from Twilio
5. Limit conversation_history to prevent memory leak

**HIGH (Fix Soon):**
6. Make TTS processing concurrent
7. Add timeout for WebSocket start event
8. Add Deepgram error event handler

**MODERATE (Nice to Have):**
9. Reduce TTS timeout from 30s to 5s
10. Add "mark" event handling for audio tracking
11. Add metadata event handler for debugging
12. Improve task cancellation for graceful shutdown