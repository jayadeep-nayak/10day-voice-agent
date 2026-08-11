# Voice Agent Starter — Powered by Murf Falcon

Build a production voice AI agent in 5 minutes. Powered by the fastest TTS on the market - swap the system prompt to build anything from customer support to language tutors.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## Why Murf Falcon

- **55ms model latency** - fastest production TTS
- **130ms time-to-first-audio** across 10+ global regions
- **$0.01/1000 characters** - up to 10x cheaper than alternatives
- **150+ voices** across 35+ languages
- **99.38% pronunciation accuracy**

---

## Architecture

```mermaid
flowchart LR
    A[🎙️ User speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[LLM]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit]
    E -->|stream| F[🔊 User hears]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#444441,stroke:#888780,color:#fff
```

---

## Quickstart

### Prerequisites

- **Python** 3.10+
- **[uv](https://docs.astral.sh/uv/)** - fast Python package manager
  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Node.js** 18+
- **pnpm** — fast Node package manager
  ```bash
  npm install -g pnpm
  ```
- A [LiveKit](https://cloud.livekit.io/) project (free tier available)

### Step 1: Clone the repo

```bash
git clone https://github.com/murf-ai/murf-livekit-starter.git
cd murf-livekit-starter
```

### Step 2: Set up environment variables

Create `.env.local` in both `backend/` and `frontend/` (copy from `.env.example` in each). You need:

| Variable                               | Where to get it                                        | Required |
| -------------------------------------- | ------------------------------------------------------ | -------- |
| `LIVEKIT_URL`                          | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_KEY`                      | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_SECRET`                   | LiveKit Cloud dashboard                                | Yes      |
| `MURF_API_KEY`                         | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) | Yes      |
| `DEEPGRAM_API_KEY`                     | [deepgram.com](https://deepgram.com)                   | Yes      |
| `GOOGLE_API_KEY` (or `OPENAI_API_KEY`) | Depends on LLM choice                                  | Yes      |

### Step 3: Install backend dependencies

```bash
cd backend
uv sync
uv run python src/agent.py download-files
```

### Step 4: Install frontend dependencies

```bash
cd frontend
pnpm install
```

### Step 5: Run it

**Option A - All-in-one (from repo root):**

```bash
# macOS/Linux
chmod +x start_app.sh
./start_app.sh

# Windows (PowerShell)
.\start_app.ps1
```

**Option B - Separate terminals:**

```bash
# Terminal 1 — LiveKit Server
livekit-server --dev

# Terminal 2 — Backend agent
cd backend && uv run python src/agent.py dev

# Terminal 3 — Frontend
cd frontend && pnpm dev
```

Then open **http://localhost:3000** in your browser.

You should now see the voice agent UI. Click **Start talking**, allow microphone access, and speak — the agent will respond with Murf Falcon TTS. Ensure your backend and (if using Option B) LiveKit server are running.

---

## Deploy

Want to deploy this beyond localhost? You'll need to deploy **two services**: the backend agent and the frontend. Both must use the same LiveKit project.

> This is a two-service app — the backend agent and the frontend UI deploy separately. You'll need both running and connected to the same LiveKit project.

### Backend (Python agent) — Deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:

- `MURF_API_KEY`
- `DEEPGRAM_API_KEY`
- `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

The backend runs as a long-lived Python process that connects to LiveKit as an agent. Railway handles this well.

### Frontend (Next.js) — Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/murf-ai/murf-livekit-starter&root-directory=frontend&env=LIVEKIT_URL,LIVEKIT_API_KEY,LIVEKIT_API_SECRET&project-name=murf-voice-agent&repository-name=murf-voice-agent)

Set these environment variables in Vercel:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `AGENT_NAME` (optional — for explicit agent dispatch)

The frontend is a standard Next.js app. Point it at the same LiveKit instance your backend agent is connected to.

### Connecting them

The frontend and backend don't call each other directly — they both connect to **LiveKit**, which handles the real-time audio transport.

1. Use the **same** `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` on both Railway and Vercel
2. Set `AGENT_NAME=my-agent` on Vercel — this matches the `agent_name="my-agent"` registered in `backend/src/agent.py`
3. Verify: Railway logs should show the agent connected to LiveKit. Open your Vercel URL, click **Start talking** — the agent should respond

If the agent doesn't connect, double-check that both services point to the same LiveKit project and that the backend is running (check Railway logs).

---

## Change the Use Case

The default system prompt makes this a **customer support agent**. You can change the agent’s behavior by editing the prompt.

**Where the prompt lives:** `backend/src/agent.py`- the `SYSTEM_PROMPT` constant (near the top of the file, after the imports). Change that string to change what your voice agent does.

### Example prompts (copy-paste)

**Customer Support (default):**

```
You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate.
```

**Language Tutor:**

```
You are a patient and encouraging language tutor helping the user practice conversational Spanish. Speak primarily in Spanish but switch to English to explain grammar or vocabulary when needed. Correct mistakes gently and suggest better phrasing. Keep conversations natural and fun.
```

**AI Receptionist:**

```
You are a professional receptionist for a medical clinic. Help callers schedule appointments, answer questions about office hours and services, and take messages for doctors. Be warm but efficient. Ask for the caller's name and reason for calling upfront.
```

See the Configuration section below for voice, STT, and LLM options.

---

## Configuration

### Murf voice

Edit the `tts=murf.TTS(...)` call in `backend/src/agent.py`. Set the `voice` argument to any Murf voice ID. Examples:

- `Anisha` — Indian English (female, default in this starter)
- `Pooja` — Indian English (female)
- `Samar` — Indian English (male)
- `Amara` — US English (female)
- `Gordon` — US English (male)
- `Hazel` — UK English (female)
- `Bertie` — UK English (male)

Browse all voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT provider

STT is configured in `backend/src/agent.py` in the `AgentSession(stt=...)` call. The default is Deepgram (`deepgram.STT(model="nova-3")`). You can swap to another LiveKit-compatible STT plugin if needed.

### LLM (Gemini vs OpenAI)

- **Gemini (default):** Set `GOOGLE_API_KEY` and use `llm=google.LLM(model="gemini-3.5-flash-lite")` in `agent.py`.
- **OpenAI:** Set `OPENAI_API_KEY`, add the OpenAI plugin, and use the corresponding `llm=openai.LLM(...)` in `agent.py`.

### Audio format

Murf Falcon and LiveKit handle audio format internally. For advanced options, see [Murf API docs](https://murf.ai/api/docs) and [LiveKit docs](https://docs.livekit.io).

---

## Project Structure

```
murf-livekit-starter/
├── backend/                 # Python voice agent (LiveKit Agents + Murf Falcon)
│   ├── src/
│   │   └── agent.py         # Agent entrypoint, pipeline (STT/LLM/TTS), system prompt
│   ├── tests/               # Agent tests
│   ├── .env.example         # Backend env template
│   ├── pyproject.toml       # Python deps (uv)
│   └── railway.toml         # Railway deploy config
├── frontend/                # Next.js UI for voice sessions
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   └── api/token/       # LiveKit token endpoint (dev)
│   ├── components/          # UI (agents-ui, app config, theme)
│   ├── app-config.ts        # Branding, title, button text, accent
│   ├── .env.example         # Frontend env template
│   └── package.json         # Node deps (pnpm)
├── start_app.sh             # Start LiveKit + backend + frontend (macOS/Linux)
├── start_app.ps1            # Start LiveKit + backend + frontend (Windows)
├── README.md                # This file
```

For deeper documentation on each part, see:

- [Backend Documentation](./backend/README.md) — agent pipeline, voice/LLM/STT configuration, testing, deployment
- [Frontend Documentation](./frontend/README.md) — UI customization, visualizers, theming, component architecture

---

## Links

- [Murf API Docs](https://murf.ai/api/docs)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Docs](https://docs.livekit.io)
- [Deepgram Docs](https://developers.deepgram.com)
- [Murf Falcon Benchmarks](https://murf.ai/falcon/benchmarks)
- [TTS Latency Benchmarker](https://github.com/sahilsgupta/tts-latency-benchmarker) — run your own p50/p95 tests across providers
- [Murf Discord](https://discord.gg/FbKAy96Sz7)
- [Murf Startup Incubator](https://murf.ai/api) — 50M free characters for startups

---

## Learning & Literacy Track: Domain Data & Tools

### Theme & Objective
- **Track**: Learning & Literacy
- **Objective**: Fetch next level-graded exercise dynamically and score a spoken answer using real domain data.

### Domain Data Sources
1. **Live External API**: [Datamuse Public Educational API](https://api.datamuse.com/words) — Fetches dynamic vocabulary, phonics, and reading definitions with a 3.5s timeout.
2. **Local Graded Dataset**: Curated Literacy & Numeracy exercise repository indexed by grade levels (`beginner`, `grade_1`, `grade_2`, `grade_3`, `intermediate`, `advanced`) and topics (`reading`, `phonics`, `vocabulary`, `math_literacy`).

### Function Calls Implemented
1. `fetch_next_exercise(level, topic)`
   - **Description**: Fetches the next exercise for the specified level and topic from the live educational API or local dataset.
   - **Data Timestamp**: Embeds ISO UTC timestamp (e.g. `2026-08-10 18:52 UTC`) stored in database records and tool payload for auditing, kept silent during voice output.
   - **Out-Loud Failure Handling**: If the API times out or network connection fails, catches the error and returns an explicit instruction so the agent announces out loud: *"I couldn't reach the online exercise server right now due to a network connection delay, so I have loaded a backup practice question from our offline curriculum."*

2. `score_spoken_answer(spoken_answer, exercise_id, expected_answer)`
   - **Description**: Evaluates character distance (Levenshtein), word overlap ratio, and phonetic similarity between the user's spoken answer and expected text.
   - **Data Timestamp**: Includes evaluation timestamp (`scored_at_timestamp`) stored in database records.

### Recommended Questions to Ask the Voice Agent

To test these function calls in action, ask the voice agent:

1. **To fetch an exercise:**
   - *"Can you give me a Grade 1 math exercise?"*
   - *"Fetch a beginner reading practice question for me."*
   - *"Give me a Grade 2 vocabulary question."*

2. **To submit & score a spoken answer:**
   - *"My answer is 'hat'. How did I do?"*
   - *"I read it as: 'The sun shines bright in the sky'. Score my reading."*
   - *"My answer for the math question is 5."*

3. **To test caller context & end-of-chat data consent:**
   - *"My name is Ramesh and we practiced beginner phonics."*
   - Agent asks at chat ending: *"I'd like to remember your name Ramesh and that we spoke about beginner phonics. Is it okay if I save this?"*
   - User responds: *"Yes, please save it."* (Triggers `save_caller_facts`)

---

## Daily Literacy Practice — Outbound Call Feature (Linphone)

This starter project includes an outbound SIP-telephony dialing feature to call users for their scheduled daily literacy practice using **Linphone** (a free, open-source SIP client).

### Outbound Call Setup & Run

#### 1. Create a Free Linphone Account
- Sign up for a free SIP account at [subscribe.linphone.org](https://subscribe.linphone.org/).
- Install the Linphone app (desktop or mobile) and sign in. Your SIP address will be: `sip:<username>@sip.linphone.org`.
- Keep the app running and online.

#### 2. Configure LiveKit Outbound Trunk
- In the [LiveKit Cloud Dashboard](https://cloud.livekit.io) -> select your project -> **SIP** tab.
- Click **Create Outbound Trunk**:
  - **Name**: `linphone-outbound`
  - **Address/Hostname**: `sip.linphone.org`
  - **Numbers**: `+0000000000` (placeholder caller ID)
- Save the trunk and copy the generated **Trunk ID** (e.g. `ST_xxxxxxxxxxxx`).

#### 3. Update Environment variables
Open `backend/.env.local` and add:
```env
SIP_OUTBOUND_TRUNK_ID=ST_xxxxxxxxxxxx             # Your LiveKit Outbound Trunk ID
LINPHONE_SIP_URI=sip:<username>@sip.linphone.org  # Your Linphone destination URI
```

#### 4. Run the Agent and Trigger the Call
- **Start the Agent (Terminal 1)**:
  ```bash
  cd backend
  uv run python src/agent.py dev
  ```
- **Trigger the Outbound Call (Terminal 2)**:
  ```bash
  cd backend
  uv run python src/make_outbound_call.py
  ```

Your Linphone client will ring. Accept the call to begin your practice!

### Supported Call Flows & Prompts

1. **Required Outbound Greeting**:
   Immediately upon pickup, the agent speaks:
   > *"Hi, this is your Daily Literacy Coach calling for your scheduled reading practice. If you want to stop these calls at any time, just say 'cancel my calls'."*
   
   If you have a returning profile in the database, the agent dynamically appends personalization based on your last lesson (e.g. *"Namaste Jay, last time we spoke about beginner English. Did the practice help?"*).

2. **Cancel Calls / Opt-Out**:
   If you say *"cancel my calls"*, *"unsubscribe"*, or *"stop calling me"*, the agent calls the `cancel_daily_calls` tool to record your opt-out, states an confirmation message, and gracefully disconnects the call.

3. **Wrap-up Consent**:
   Immediately after the first exercise is completed and scored, the agent wraps up the call and asks:
   > *"I'd like to remember your name {Name} and that we spoke about {Topic}. Is it okay if I save this?"*
   
   Responding *"Yes"* saves your details to `voice_agent.db` for the next call's personalization.

---

## License

MIT


