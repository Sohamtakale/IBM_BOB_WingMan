# WingMan Demo Scenario: Dentist Appointment Rescheduling

## Demo Setup

**Scenario**: You need to reschedule your dentist appointment from Wednesday 3 PM to next Tuesday at 10 AM, but you're in a meeting and can't call yourself.

**Test Numbers** (Twilio trial verified):
- Primary: `+917058809304`
- Backup: `+919579560024`

**Demo Flow Duration**: ~90 seconds total

---

## Step-by-Step Demo Script

### Phase 1: Voice Setup (20 seconds)

**You say to WingMan:**
> "Call Dr. Smith's dental office and reschedule my Wednesday 3 PM appointment to next Tuesday at 10 AM"

**What happens on screen:**
1. Particle orb activates (listening mode - fast rotation)
2. Your speech appears as text in real-time
3. WingMan asks: "Got it. Fill in their details —"
4. Contact form appears with:
   - Name: "Dr. Smith's Office" (pre-filled from voice)
   - Phone: `+917058809304` (you type this)

**You click:** "Continue →"

### Phase 2: Message Confirmation (15 seconds)

**WingMan says:**
> "Got it. I'll call Dr. Smith's Office and say: Reschedule my Wednesday 3 PM appointment to next Tuesday at 10 AM. You can edit below, then tap call."

**What's on screen:**
```
TO: Dr. Smith's Office · +917058809304

MESSAGE:
Reschedule my Wednesday 3 PM appointment to next Tuesday at 10 AM
```

**You click:** "📞 Call now"

### Phase 3: Live Call (45 seconds)

**Screen shows:**
- Green pulsing dot (call active)
- "Dr. Smith's Office · +917058809304 · In progress"
- Live transcript box with real-time updates

**Expected Conversation Flow:**

```
🤖 WingMan:
"Hi! I'm WingMan, Soham's AI assistant. I'm calling to reschedule 
Soham's Wednesday 3 PM appointment to next Tuesday at 10 AM. 
Is there anything you'd like to say or ask Soham?"

🧑 Receptionist:
"Hi, this is Sarah from Dr. Smith's office. Let me check the schedule... 
Yes, we have Tuesday at 10 AM available. Can I confirm the patient name?"

🤖 WingMan:
"Yes, it's Soham. Should I have him confirm anything else?"

🧑 Receptionist:
"No, that's perfect. We've rescheduled the appointment. 
Is there anything else?"

🤖 WingMan:
"No, that's all. Thank you so much for your help!"

🧑 Receptionist:
"You're welcome! Have a great day."

🤖 WingMan:
"Goodbye!"
```

**What judges should notice:**
- Transcript appears in real-time as conversation happens
- Natural back-and-forth dialogue
- WingMan handles unexpected questions smoothly
- Polite, professional tone throughout
- Automatic goodbye detection

### Phase 4: Call Complete (10 seconds)

**Screen updates:**
- Status changes to "Completed"
- Summary appears: "Call completed. Appointment rescheduled successfully."
- Two buttons appear:
  - "See debrief →" (Coach report)
  - "Dashboard"

**WhatsApp notification arrives:**
```
Call with Dr. Smith's Office is done.

✅ Message delivered successfully

What they said:
- Confirmed Tuesday 10 AM is available
- Appointment has been rescheduled
- Patient name confirmed: Soham

No action items needed - you're all set!
```

---

## Alternative Conversation Paths

### If Receptionist Asks for More Details

```
🧑 Receptionist:
"What's the reason for the appointment?"

🤖 WingMan:
"I'm not sure — I'll let Soham know you asked. 
Is there anything else you need?"
```

**Key Point**: WingMan admits when it doesn't know, doesn't make up information.

### If Time Slot Not Available

```
🧑 Receptionist:
"Tuesday at 10 AM is booked. We have 11 AM or Wednesday at 2 PM?"

🤖 WingMan:
"Let me note that down. I'll have Soham call back to confirm 
which time works. Is there anything else?"
```

**Key Point**: WingMan handles unexpected situations gracefully.

### If Voicemail

```
🤖 WingMan:
"Hi, this is WingMan calling on behalf of Soham to reschedule 
his Wednesday 3 PM appointment to next Tuesday at 10 AM. 
Please call back at [your number]. Thank you!"
```

**Key Point**: WingMan detects voicemail and leaves appropriate message.

---

## Demo Talking Points During Call

While the call is happening, point out to judges:

1. **"Notice the live transcript updating in real-time"**
   - Shows WebSocket streaming working
   - Demonstrates Deepgram STT accuracy

2. **"Watch how WingMan handles the back-and-forth naturally"**
   - Not just reading a script
   - Responding to questions contextually
   - Using conversation history

3. **"See how it keeps the conversation open"**
   - Always ends with "Anything else?" or similar
   - Doesn't rush to hang up
   - Only says goodbye when receptionist is done

4. **"The latency is under 1.5 seconds"**
   - Receptionist finishes speaking → WingMan responds
   - Feels natural, not robotic
   - Thanks to streaming LLM optimization

---

## Post-Demo: Show Coach Report

**Click "See debrief →"**

**Coach Report shows:**

```
Confidence Score: 92/100
Goal Achievement: ✅ Achieved (95/100)

What You Crushed:
✓ Clear communication of the rescheduling request
✓ Professional and polite tone throughout
✓ Handled receptionist's questions smoothly
✓ Confirmed all necessary details

Real Talk (What to Improve):
• Could have proactively offered alternative times
• Might have asked for confirmation email

Next Time:
→ When rescheduling, offer 2-3 backup time slots
→ Request written confirmation for important appointments
→ Consider asking about cancellation policy

Summary:
Successfully rescheduled appointment with Dr. Smith's office. 
Receptionist was helpful and confirmed Tuesday 10 AM availability. 
No follow-up action required.
```

---

## Backup Demo Plan (If Call Fails)

**Have screenshots/video ready showing:**
1. Voice setup flow
2. Live transcript of a previous successful call
3. WhatsApp summary
4. Coach report

**Talking points:**
- "This is what a successful call looks like"
- "Here's the real-time transcript from our test"
- "And here's the WhatsApp summary users receive"

---

## Technical Highlights to Mention

### During Setup Phase:
"Notice we're using Web Speech API for voice input — no typing required until you want to edit."

### During Call Phase:
"Under the hood, we're streaming audio through Twilio WebSockets, transcribing with Deepgram Nova-2, processing with Groq's Llama 3.1, and synthesizing speech with Deepgram Aura — all in real-time."

### During Transcript Display:
"We implemented streaming LLM responses — WingMan starts speaking while the model is still generating. This cuts latency by 50%."

### After Call:
"The WhatsApp summary is generated by analyzing the full transcript with context about the original message and user profile."

---

## Common Questions & Answers

**Q: What if the person doesn't answer?**
A: WingMan detects voicemail and leaves an appropriate message. We also handle busy signals and failed connections gracefully.

**Q: Can it handle accents?**
A: Yes, Deepgram Nova-2 is trained on diverse accents. We've tested with Indian, American, and British English successfully.

**Q: What about privacy?**
A: No audio recordings are stored. Transcripts are temporary in-memory. WhatsApp messages use end-to-end encryption.

**Q: How much does it cost per call?**
A: Approximately $0.15-0.25 per call (Twilio + Deepgram + Groq). Much cheaper than a virtual assistant at $30/hour.

**Q: Can businesses use this?**
A: Absolutely. Imagine automating appointment confirmations, follow-up calls, or customer service callbacks.

---

## Demo Checklist

**Before Demo:**
- [ ] Backend running (`uvicorn main:app --reload`)
- [ ] Frontend running (`npm run dev`)
- [ ] Test call to verified number works
- [ ] WhatsApp configured and tested
- [ ] Browser microphone permissions granted
- [ ] Volume up for judges to hear TTS
- [ ] Backup screenshots/video ready
- [ ] Timer ready (aim for 90 seconds)

**During Demo:**
- [ ] Speak clearly into microphone
- [ ] Point to screen elements as they appear
- [ ] Narrate what's happening
- [ ] Show enthusiasm and confidence
- [ ] Watch for judge reactions

**After Demo:**
- [ ] Show WhatsApp summary on phone
- [ ] Navigate to Coach report
- [ ] Offer to answer technical questions
- [ ] Have architecture diagram ready if needed

---

## Success Metrics

**Demo is successful if judges see:**
1. ✅ Voice-driven setup working smoothly
2. ✅ Call connects and conversation starts
3. ✅ Live transcript updating in real-time
4. ✅ Natural back-and-forth dialogue
5. ✅ Call completes with summary
6. ✅ WhatsApp notification received
7. ✅ Coach report with insights

**Bonus points if:**
- Receptionist asks unexpected question (shows adaptability)
- Latency is noticeably fast
- Judges comment on naturalness
- WhatsApp summary is detailed and accurate