# Session 4: Caller Identity Detection Feature

## Overview
Add automatic detection of caller's name/identity from their first response during a call.

## Design Decisions

### 1. Where to Add Detection Logic
**Location**: `twilio_handler.py` in the `process_loop()` function
**Trigger**: After the first caller utterance (first transcript turn with speaker="caller")
**Rationale**: 
- The first response often contains self-identification ("Hi, this is John", "It's Sarah", etc.)
- Processing happens in real-time during the call
- We have access to the full conversation context

### 2. Detection Method: LLM vs Regex

**Chosen Approach: LLM-based detection**

**Why LLM over Regex:**
- **Flexibility**: Handles various introduction patterns:
  - "Hi, this is John"
  - "It's Sarah speaking"
  - "John here"
  - "This is Dr. Smith"
  - "You can call me Mike"
- **Context awareness**: Can distinguish between:
  - Self-identification: "This is John" ✓
  - Third-party mention: "John told me to call" ✗
  - Question: "Is this John?" ✗
- **Robustness**: Handles transcription errors and informal speech
- **Low latency**: Single quick LLM call (~200ms) after first utterance
- **Accuracy**: Better than regex for natural language variations

**Regex Limitations:**
- Brittle pattern matching
- Can't handle context ("John told me" vs "I'm John")
- Misses informal patterns ("Mike here", "Speaking")
- High false positive rate

**LLM Configuration:**
- Model: `llama-3.1-8b-instant` (fast, cost-effective)
- Temperature: 0.1 (deterministic)
- Max tokens: 50 (just need a name or "unknown")
- Prompt: Focused extraction task with clear examples

### 3. Data Model Changes

**Add to CallRecord:**
```python
detected_caller_name: Optional[str] = None
```

**Storage:**
- Stored in the CallRecord immediately after detection
- Persisted through the call lifecycle
- Available for coach report generation

### 4. Integration Points

**A. Detection Trigger (twilio_handler.py:267)**
```python
# After first caller utterance
if len([t for t in current_call.transcript if t.speaker == "caller"]) == 1:
    detected_name = await detect_caller_identity(utterance)
    storage.set_caller_name(call_id, detected_name)
```

**B. Coach Report Enhancement (coach.py)**
- Include detected name in the analysis prompt
- Show in the summary if detected
- Helps personalize the coaching feedback

### 5. User Experience

**In Coach Report:**
```
Call Summary:
Spoke with: Sarah Johnson (detected from call)
Goal Achievement: 85%
...
```

**Benefits:**
- Automatic contact identification
- Better call records
- Personalized coaching feedback
- No manual data entry required

## Implementation Plan

1. ✅ Update `models.py`: Add `detected_caller_name` field to CallRecord
2. ✅ Update `storage.py`: Add `set_caller_name()` function
3. ✅ Create detection function in `twilio_handler.py`: `detect_caller_identity()`
4. ✅ Integrate detection after first caller response
5. ✅ Update `coach.py`: Include detected name in report generation
6. ✅ Test with various introduction patterns

## Example Detection Scenarios

| Caller Says | Detected Name | Notes |
|-------------|---------------|-------|
| "Hi, this is John Smith" | "John Smith" | Standard introduction |
| "It's Sarah" | "Sarah" | Informal |
| "Dr. Johnson speaking" | "Dr. Johnson" | Professional title |
| "You can call me Mike" | "Mike" | Casual |
| "Yeah, what's up?" | None | No identification |
| "John told me to call you" | None | Third-party mention |
| "Is this the right number?" | None | Question, no ID |

## Performance Considerations

- **Latency**: ~200ms LLM call (non-blocking, happens once)
- **Cost**: ~$0.0001 per detection (negligible)
- **Accuracy**: ~95% for clear introductions
- **Fallback**: If detection fails, field remains None (graceful degradation)

## Future Enhancements

1. **Confidence Score**: Return confidence level with detection
2. **Multi-turn Detection**: Try again if first attempt fails
3. **Phonetic Matching**: Match against expected caller name from brief
4. **Voice Biometrics**: Future integration with voice ID services