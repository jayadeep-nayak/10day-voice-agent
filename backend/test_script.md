# 🎬 Test Script — Human Escalation Recording

Two conversations to demonstrate both paths: one that triggers escalation and one that doesn't.

---

## 🔴 Conversation A — Escalation Path (Learner Is Upset)

> **Goal**: The learner gets frustrated during a reading exercise → agent detects distress → empathizes → asks for database permission → creates escalation → gives reference ID.

| # | Speaker | What to Say |
|---|---------|-------------|
| 1 | **Nova (Agent)** | *"Hi! How can I help you today? Feel free to speak with me in English or Hindi! May I know your name?"* |
| 2 | **You (Learner)** | **"Hi, my name is Ravi."** |
| 3 | **Nova** | *"Hi Ravi! Welcome! What would you like to practice today? We can do reading, vocabulary, or math."* |
| 4 | **You** | **"I want to try a reading exercise."** |
| 5 | **Nova** | *(Calls `fetch_next_exercise`)* *"Great! Here's your exercise: Read this sentence aloud — 'The cat sat on the mat.'"* |
| 6 | **You** | **"The... cat... s-sat... I don't know... this is too hard! I can't do this! I give up!"** |
| 7 | **Nova** | *(Detects upset)* *"I completely understand, Ravi. Sometimes it helps to talk to a real teacher who can sit with you and explain things step by step. Let me help connect you."* |
| 8 | **Nova** | *"I would like to save a short note in our system with your name, what we were working on, your language, and how you'd like to be contacted — so a teacher can reach out to you. Would you like me to store this in the database, or not?"* |
| 9 | **You** | **"Yes, please save it. I want a teacher to call me back."** |
| 10 | **Nova** | *(Calls `create_escalation`)* *"Your request has been saved. Your reference number is ESC-20260812-0001. A teacher will review this and reach out to you within 24 hours. You did a great job trying today, Ravi. Don't give up!"* |
| 11 | **You** | **"Thank you, Nova."** |
| 12 | **Nova** | *"You're welcome, Ravi! Remember, every great reader started exactly where you are. Take care!"* |

### ✅ What to Verify (Conversation A)
- Agent detected frustration ("I can't do this", "I give up")
- Agent empathized before asking
- Agent explicitly asked: "Would you like me to store this in the database, or not?"
- Agent called `create_escalation` only AFTER user said "Yes"
- Agent gave reference ID (ESC-YYYYMMDD-NNNN)
- Agent said "within 24 hours" (no false promise of immediate reply)
- Escalation appears on dashboard at http://localhost:5050

---

## 🟢 Conversation B — Normal Path (No Escalation)

> **Goal**: The learner completes a normal exercise successfully. Agent does NOT escalate.

| # | Speaker | What to Say |
|---|---------|-------------|
| 1 | **Nova (Agent)** | *"Hi! How can I help you today? Feel free to speak with me in English or Hindi! May I know your name?"* |
| 2 | **You (Learner)** | **"Hello! I'm Priya."** |
| 3 | **Nova** | *"Hi Priya! What would you like to practice today?"* |
| 4 | **You** | **"Can I do a vocabulary exercise?"** |
| 5 | **Nova** | *(Calls `fetch_next_exercise`)* *"Sure! Here's your exercise: What is the opposite of 'hot'?"* |
| 6 | **You** | **"Cold!"** |
| 7 | **Nova** | *(Calls `score_spoken_answer`)* *"That's correct! Great job, Priya! You scored 100%! Would you like to try another exercise?"* |
| 8 | **You** | **"No thanks, that's enough for today."** |
| 9 | **Nova** | *"I'd like to remember your name Priya and that we spoke about vocabulary. Is it okay if I save this?"* |
| 10 | **You** | **"Yes, go ahead."** |
| 11 | **Nova** | *(Calls `save_caller_facts`)* *"Saved! Great session today, Priya. Keep up the good work! Bye!"* |

### ✅ What to Verify (Conversation B)
- Agent did NOT mention escalation at any point
- Agent did NOT call `create_escalation`
- Normal exercise flow worked (fetch → score → save)
- No new escalation appeared on the dashboard

---

## 🔴 Bonus Conversation C — Escalation Declined (User Says No)

> **Goal**: Learner asks for a teacher but declines database storage.

| # | Speaker | What to Say |
|---|---------|-------------|
| 1 | **Nova (Agent)** | *"Hi! How can I help you today?"* |
| 2 | **You (Learner)** | **"I want to talk to a real teacher. Can you get me a teacher?"** |
| 3 | **Nova** | *(Detects teacher request)* *"Of course! I understand. Sometimes it's really helpful to speak with a real teacher. I would like to save a short note in our system with your name and what we were working on, so a teacher can reach out to you. Would you like me to store this in the database, or not?"* |
| 4 | **You** | **"No, don't save anything."** |
| 5 | **Nova** | *"Okay, I won't store anything. Is there anything else I can help you with today?"* |
| 6 | **You** | **"No, thank you. Bye."** |
| 7 | **Nova** | *"Goodbye! Feel free to come back anytime you need help. Take care!"* |

### ✅ What to Verify (Conversation C)
- Agent detected "I want to talk to a teacher"
- Agent asked for database permission
- User said "No, don't save anything"
- Agent did NOT call `create_escalation`
- No new escalation appeared on the dashboard

---

## 🚀 How to Run the Test

1. **Start the dashboard** (in a separate terminal):
   ```
   cd backend/src
   python escalation_dashboard.py
   ```
   Open http://localhost:5050 — should show "No Open Requests"

2. **Start the voice agent** (in another terminal):
   ```
   cd backend
   python -m livekit.agents dev src/agent.py
   ```

3. **Open the frontend** and connect to the agent.

4. **Run Conversation A** — say the lines from the script above.
   After it ends, refresh http://localhost:5050 — you should see Ravi's escalation.

5. **Run Conversation B** — say the lines from the script above.
   Refresh dashboard — NO new escalation should appear.

6. **(Optional) Run Conversation C** — to show the "declined" path.
