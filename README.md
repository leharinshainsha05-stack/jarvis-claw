---

## ✨ Features

### 🎙️ Voice & Wake Word
- Say **"Hey Jarvis"** anywhere → Jarvis wakes up instantly
- Inline commands: *"Hey Jarvis open YouTube"* in one breath
- Tkinter overlay with live status + brain indicator

### 🧠 Dual-Brain Routing
- Every input → **Semantic Router** (sentence-transformer embeddings)
- Emotional/personal queries → **Personal Brain** (local Ollama + ChromaDB)
- Technical/general queries → **General Brain** (Groq Llama 3 70B → HTTP fallback → local Ollama)

### ⚡ Commands (v1 Core)
| Command | Action |
|---------|--------|
| `play [song]` | Opens Spotify |
| `youtube [query]` | Opens Edge browser |
| `search google for [query]` | Google search |
| `open [site]` | Instagram, Gmail, GitHub, Netflix, Amazon, Flipkart, Spotify |
| `send message to [name] saying [text]` | WhatsApp with confirmation gate |
| `call [name]` / `video call [name]` | WhatsApp call |
| `email to [address] subject [x] body [y]` | Gmail SMTP |
| `remind me in [n] minutes to [task]` | Local reminder |
| `shutdown` / `restart` / `sleep` / `cancel` | System control |
| `time` / `date` | Current time/date |

### 🤖 Autonomous Action Agent (v2)
| Command | Action |
|---------|--------|
| `book train ticket` | Opens IRCTC, asks from/to/date, fills details |
| `book flight` | MakeMyTrip automation |
| `book cab` | Uber automation |
| `order food` | Swiggy/Zomato automation |
| `edit video` | Finds CapCut/DaVinci on PC, opens + guides |
| `pay bill` | PhonePe automation |
| `recharge phone` | Paytm automation |
| `buy on amazon/flipkart` | Searches with your item |

### 💜 Personal Brain
- **ChromaDB** vector store — stores every personal conversation
- Sentiment tagging: `Happy` `Sad` `Angry` `Anxious` `Motivated` `Betrayal` `Love` `Neutral`
- Emotional continuity — references past conversations naturally
- **100% local** — zero data leaves your device

### ⚡ General Brain
- **Groq API** (Llama 3 70B) — GPT-4 level reasoning
- **Self-Correction Loop** — 3 retry attempts for code debugging
- Falls back to local **Ollama** if Groq is offline

### 🌅 Agentic Core
| Feature | Description |
|---------|-------------|
| **Morning Brief** | Greeting + nightly goals + calendar + deadlines + GitHub alerts + motivator |
| **Nightly Recap** | Triggered by "goodnight" — recaps today, collects tomorrow's goals |
| **Deadline Manager** | Proactive alerts every minute — 3 days / 1 day / overdue |
| **CrewAI Orchestrator** | Planner → Executor → Reviewer three-agent pipeline |

### 👁️ Screen Vision
- Say **"check my screen"** → screenshot → LLaVA analyzes → speaks result
- Proactive error detection — detects terminal errors automatically

### 🌍 Multilingual
- Tamil script → responds in Tamil
- Hindi / Telugu / Malayalam / Kannada → auto-detected by Unicode block analysis

### 🔗 Integrations
- **Google Calendar** — reads your schedule (requires `credentials.json`)
- **GitHub Monitoring** — watches CI, PRs, merge conflicts (requires `GITHUB_TOKEN`)
- **n8n Automation** — Gmail, WhatsApp via Twilio, task creation (port 5678)
- **Confirmation gate** on all outbound actions

### 🖥️ Frontend (Stark HUD)
- CSS Grid, fully responsive (desktop / tablet / mobile)
- Live brain indicator — shows which brain answered
- Activity log — every action logged in real time
- Memory Browser — full conversation archive sorted by emotion folder
- Brief Page (`brief.html`) — Morning Brief + Things To Do + Things To Complete
- Deadlines panel with urgency badges
- Date navigation for brief history

---

