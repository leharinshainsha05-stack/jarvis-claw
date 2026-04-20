<div align="center">

# 🤖 JARVIS v2.0
### Voice-First Agentic Personal OS

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-Llama3_70B-orange?style=for-the-badge)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-green?style=for-the-badge)](https://chromadb.com)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi_Agent-purple?style=for-the-badge)](https://crewai.com)
[![n8n](https://img.shields.io/badge/n8n-Automation-red?style=for-the-badge)](https://n8n.io)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> **"Not just a voice assistant — a full Agentic OS that perceives, reasons, and acts."**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Testing](#-testing) • [Agentic Standard](#-agentic-standard)

</div>

---

## 📸 Preview

> Stark HUD frontend with dual-brain indicator, Arc Reactor animation, live activity log, and emotion-sorted memory browser.

---

## 🧠 What is JARVIS?

JARVIS is a **privacy-first, voice-activated agentic assistant** that runs on your local machine. Unlike conventional AI assistants, JARVIS is not a simple chatbot. It is a full operating-system-layer agent capable of:

- Understanding **intent** via semantic routing
- Routing conversations to the **right brain** (personal or general)
- **Executing cross-app commands** autonomously (WhatsApp, Spotify, IRCTC, Uber, Swiggy)
- **Maintaining deeply personal memory** encrypted locally via ChromaDB
- **Proactively planning your day** before you ask — Morning Brief, Nightly Recap, Deadline alerts
- **Self-correcting** when code fixes fail — 3-attempt loop before escalating

---

## ✨ Features

### 🎙️ Voice & Wake Word
- Say **"Hey Jarvis"** anywhere → Jarvis wakes up instantly
- Inline commands: *"Hey Jarvis open YouTube"* in one breath
- Tkinter floating overlay with live status + brain indicator

### 🧠 Dual-Brain Architecture

```
Voice Input → Whisper STT → Semantic Router
                                   ↓
              ┌────────────────────────────────────┐
              │ PERSONAL BRAIN    │  GENERAL BRAIN │
              │ (Ollama + Chroma) │  (Groq API)    │
              │ Emotional support │  Debugging      │
              │ Memory-enabled    │  Research       │
              │ 100% local        │  Self-corrects  │
              └────────────────────────────────────┘
```

### ⚡ Voice Commands

| Command | Action |
|---------|--------|
| `play [song]` | Spotify |
| `youtube [query]` | Edge browser |
| `search google for [query]` | Google search |
| `open [site]` | Instagram, Gmail, GitHub, Netflix, Amazon, Flipkart |
| `send message to [name] saying [text]` | WhatsApp with confirmation gate |
| `call [name]` / `video call [name]` | WhatsApp call |
| `email to [addr] subject [x] body [y]` | Gmail SMTP |
| `remind me in [n] minutes to [task]` | Local reminder |
| `shutdown` / `restart` / `sleep` | System control |
| `time` / `date` | Current time and date |

### 🤖 Autonomous Action Agent

Uses **contextual embedding** (sentence-transformers cosine similarity) to detect intent — not brittle keyword matching.

| You say | Jarvis does |
|---------|-------------|
| `book a train ticket` | Opens IRCTC → asks from/to/date → fills form |
| `book a flight` | MakeMyTrip automation |
| `book a cab` | Uber web automation |
| `order food` | Swiggy / Zomato automation |
| `edit this video` | Finds CapCut/DaVinci on PC → opens → guides |
| `pay electricity bill` | PhonePe automation |
| `recharge my phone` | Paytm automation |
| `buy on amazon` | Amazon search automation |

### 💜 Personal Brain
- **ChromaDB** vector store — every personal conversation stored locally
- Auto sentiment tagging: `Happy` `Sad` `Angry` `Anxious` `Motivated` `Betrayal` `Love` `Neutral`
- Emotional continuity — references past conversations naturally
- Responds in **Tamil, Hindi, Telugu, Malayalam, Kannada** automatically
- **100% local — zero data leaves your device**

### ⚡ General Brain
- **Groq API** (Llama 3 70B) — GPT-4 level reasoning, ultra-low latency
- **Self-Correction Loop** — 3 retry attempts for code debugging, escalates to user if all fail
- Falls back to local **Ollama** if Groq is offline

### 🌅 Agentic Core

| Feature | Description |
|---------|-------------|
| **Morning Brief** | Greeting + nightly goals + calendar events + deadlines + GitHub alerts + motivator |
| **Nightly Recap** | Triggered by "goodnight" — recaps today, collects tomorrow's goals one by one |
| **Deadline Manager** | Proactive alerts — checks every minute, alerts at 3 days / 1 day / overdue |
| **CrewAI Orchestrator** | Planner Agent → Executor Agent → Reviewer Agent pipeline |
| **n8n Automation** | Cross-app workflows — Gmail, Calendar, WhatsApp, GitHub |

### 👁️ Screen Vision
- Say **"check my screen"** → captures screenshot → LLaVA analyzes → speaks result
- Proactive terminal error detection — detects exceptions without being asked

### 🖥️ Frontend (Stark HUD)
- CSS Grid layout — fully responsive (desktop / tablet / mobile)
- Live dual-brain indicator with active brain highlighting
- Real-time activity log
- Memory Browser — full conversation archive sorted by emotion folder
- Daily Brief page — Morning Brief + Things To Do + Things To Complete (all editable)
- Deadline panel with urgency badges (Overdue / Due Today / 3d Left)
- Date navigation for browsing past briefs

---

## 🏗️ Architecture

```
E:\jarvis-claw\
├── main.py                    ← Entry point — voice loop + WS server
├── SOUL.md                    ← Jarvis personality + directives
├── .env                       ← API keys (never committed)
│
├── router/
│   └── semantic_router.py     ← Embedding-based PERSONAL/GENERAL classifier
│
├── brain/
│   ├── personal_brain.py      ← Ollama + ChromaDB + sentiment tagging
│   └── general_brain.py       ← Groq API + self-correction loop
│
├── memory/
│   └── sqlite_memory.py       ← SQLite tasks, deadlines, reminders
│
├── agentic/
│   ├── action_agent.py        ← Autonomous task execution (IRCTC, Uber, etc.)
│   ├── morning_brief.py       ← Daily brief generator
│   ├── nightly_recap.py       ← Goal collection + storage
│   ├── deadline_manager.py    ← Proactive deadline alerts
│   ├── crew_orchestrator.py   ← CrewAI Planner/Executor/Reviewer
│   ├── calendar_integration.py← Google Calendar API
│   ├── github_monitor.py      ← GitHub CI/PR monitoring
│   ├── confirmation_gate.py   ← Ask before sending messages
│   └── n8n_integration.py     ← n8n webhook triggers
│
├── utils/
│   ├── screen_vision.py       ← LLaVA screenshot analysis
│   ├── language_detect.py     ← Tamil/Hindi/Telugu auto-detection
│   └── logger.py              ← Structured logging
│
└── jarvis-frontend/
    ├── index.html             ← Stark HUD main interface
    ├── style.css              ← Responsive CSS Grid layout
    ├── app.js                 ← WebSocket + memory browser + deadlines
    └── brief.html             ← Daily brief page
```

---

## 📋 Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Wake Word | Google Speech Recognition | Always-on, lightweight |
| STT | SpeechRecognition + sounddevice | Local processing |
| Semantic Router | sentence-transformers (all-MiniLM-L6-v2) | Embedding-based intent |
| Personal Brain | Ollama (Gemma 3 1B) | 100% local, private |
| General Brain | Groq API (Llama 3 70B) | GPT-4 level, ultra-fast |
| Vector Memory | ChromaDB | Local encrypted vector store |
| Task Memory | SQLite | Local, structured storage |
| Screen Vision | LLaVA via Ollama | Local multimodal model |
| Orchestration | CrewAI (custom) | Planner/Executor/Reviewer |
| Automation | n8n | Cross-app workflow engine |
| TTS | PowerShell Speech Synthesis | Zero latency, no API |
| Frontend | Vanilla JS + CSS Grid | Lightweight Stark HUD |

---

## 🚀 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ (for n8n)
- [Ollama](https://ollama.com) installed and running

### Step 1 — Clone the repo
```bash
git clone https://github.com/leharinshainsha05-stack/jarvis-claw.git
cd jarvis-claw
```

### Step 2 — Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### Step 3 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Pull Ollama models
```bash
ollama pull gemma3:1b      # Personal Brain (required)
ollama pull llava           # Screen Vision (optional)
```

### Step 5 — Create `.env` file
```env
GROQ_API_KEY=gsk_your_groq_key_here
GITHUB_TOKEN=ghp_your_github_token_here
MURF_API_KEY=your_murf_key_here
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
```

> Get Groq API key free at [console.groq.com](https://console.groq.com)

### Step 6 — Run
```bash
python main.py
```

Open `jarvis-frontend/index.html` in Chrome. Status bar should show `WS: CONNECTED`.

---

## 🧪 Testing

Run the full test suite before starting:

```bash
python test_jarvis.py
```

Expected output:
```
✓ Ollama server
✓ Ollama chat (gemma3:1b)
✓ Router import
✓ Personal route
✓ General route
✓ Personal Brain chat
✓ Groq API (Llama 3 70B)
✓ ChromaDB
✓ SQLite memory
✓ English detection
✓ Tamil script detection
✓ Screenshot capture
✓ Morning Brief generation
✓ CrewAI 3-agent pipeline

14 passed | 0 failed 
```

### Test Commands

| Say this | Tests this |
|----------|-----------|
| `"Hey Jarvis"` | Wake word detection |
| `"Hey Jarvis, what time is it"` | General Brain routing |
| `"I feel really sad today"` | Personal Brain + sentiment |
| `"Vanakam epdi iruka"` | Tamil language detection |
| `"Morning brief"` | Agentic Core |
| `"Book a train ticket"` | Action Agent + IRCTC |
| `"Check my screen"` | Screen Vision (LLaVA) |
| `"Goodnight"` | Nightly Recap flow |

---

## 🏆 Agentic Standard

JARVIS satisfies all three pillars of the 2026 Agentic Standard:

### Pillar 1 — Perception ✅
| Standard | JARVIS Implementation |
|----------|----------------------|
| Watching a GitHub repo | `github_monitor.py` — polls CI status, PRs, merge conflicts |
| Reading an inbox | Gmail via n8n webhook |
| Screen monitoring | `screen_vision.py` — LLaVA trigger-based screenshot analysis |
| Proactive detection | Detects terminal errors without being asked |

### Pillar 2 — Reasoning ✅
| Standard | JARVIS Implementation |
|----------|----------------------|
| Manager Agent | `crew_orchestrator.py` — Planner → Executor → Reviewer |
| Planning | Planner breaks tasks into ordered steps before execution |
| Self-correction | 3-retry loop: Attempt → Screen re-read → New approach → Escalate |
| Semantic routing | `semantic_router.py` — cosine similarity embeddings |

### Pillar 3 — Action ✅
| Standard | JARVIS Implementation |
|----------|----------------------|
| External API calls | Groq API, Google Calendar, GitHub API, n8n webhooks |
| Cross-app execution | WhatsApp, Gmail, Spotify, IRCTC, Uber, Swiggy |
| Autonomous workflows | Morning orchestration — Calendar + GitHub + Deadlines → Brief |
| Confirmation gates | Asks before every outbound action |

### Winning Criteria

| Criteria | Result |
|----------|--------|
| **Tool Integration** | Groq + GitHub + Google Calendar + n8n + WhatsApp + Gmail |
| **Self-Correction** | 3-attempt debugging loop in `general_brain.py` |
| **30-min task solved** | Train booking: 15+ min manually → 1 voice command with Jarvis |

---

## 🔒 Privacy & Security

| Data Type | Storage | Access |
|-----------|---------|--------|
| Personal conversations | Local ChromaDB only | Zero — never leaves device |
| Voice audio | Processed locally | Never stored |
| General chat history | Local SQLite | Zero external access |
| API queries | Groq servers (TLS) | API provider only |

---

## 📁 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for Llama 3 70B |
| `EMAIL_ADDRESS` | Yes | Gmail address for sending emails |
| `EMAIL_PASSWORD` | Yes | Gmail app password |
| `GITHUB_TOKEN` | Optional | GitHub Personal Access Token |
| `MURF_API_KEY` | Optional | Murf AI TTS (fallback available) |
| `N8N_BASE_URL` | Optional | n8n URL (default: http://localhost:5678) |

---

## 🗺️ Roadmap

| Phase | Status | Deliverables |
|-------|--------|--------------|
| Phase 1 — Foundation | ✅ Done | Wake word, 8 commands, Ollama, JSON memory |
| Phase 2 — Dual-Brain | ✅ Done | Groq API, Semantic Router |
| Phase 3 — Private Brain | ✅ Done | ChromaDB, sentiment tagging |
| Phase 4 — Agentic Core | ✅ Done | Morning Brief, Nightly Recap, Deadlines |
| Phase 5 — Action Agent | ✅ Done | IRCTC, Uber, Swiggy, video editing |
| Phase 6 — Vision & Language | ✅ Done | LLaVA, Tamil/Hindi/Telugu |
| Phase 7 — Perception | ✅ Done | GitHub monitoring, screen error detection |
| Phase 8 — Self-Correction | ✅ Done | LangGraph-style reasoning loop |
| Phase 9 — Orchestration | ✅ Done | CrewAI + n8n workflows |
| Phase 10 — Mobile | 🔄 Planned | iOS + Android port |

---



---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ by **Leharin S**

*"Jarvis is not a product. It is a philosophy — that technology should serve you, protect you, and grow with you."*

</div>