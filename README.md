# JARVIS — Just A Rather Very Intelligent System
> Built for the Murf.ai Hackathon 2025

## Problem Statement
Current voice assistants like Siri or Alexa are fundamentally limited — they can search the web or set timers, but they cannot execute complex, multi-step workflows on a user's local machine. For developers and power users, switching contexts between typing code, running terminal commands, and reading documentation breaks their flow state and slows down productivity.

## Solution
JARVIS is a fully voice-controlled AI desktop assistant that eliminates context switching entirely. Instead of stopping your work to open apps, type commands, or click through menus — you simply speak, and JARVIS executes the workflow on your local machine instantly.

A developer deep in code can say *"send message to teammate saying I pushed the fix"* — JARVIS opens WhatsApp, finds the contact, types the message, and sends it. Without the developer ever leaving their editor.

The key innovation is the **speak → think → act → respond** pipeline:
- You speak a command into the Stark HUD browser interface
- The frontend sends it to the Python backend via WebSocket in real time
- The backend executes the actual workflow on the local machine
- Murf.ai's natural human voice speaks the response back — not robotic TTS, but a warm intelligent voice that feels like a real assistant

The AI brain runs on **Ollama + Gemma3 completely offline** — no API limits, no internet dependency. JARVIS remembers past commands and conversations, so context is never lost between sessions.

The result is **zero context switching**. The developer stays in flow. JARVIS handles everything else.

## How It Works
1. User speaks or types a command in the Stark HUD browser interface
2. Frontend sends command to Python backend via WebSocket
3. Backend processes the command and executes it on the local machine
4. Murf.ai converts the response to natural human voice and speaks it back

## Features
- 🔊 **Murf.ai Voice** — Natural human voice output for every response
- 🎤 **Voice Input** — Speak commands via microphone
- 🤖 **Ollama AI** — Offline AI brain using Gemma3 for intelligent conversations
- 📱 **WhatsApp Automation** — Send messages and make voice/video calls
- 🌐 **Web Control** — Open YouTube, Google, Instagram, Gmail and more
- 📧 **Email** — Send emails via Gmail
- ⏰ **Reminders** — Set timed reminders
- 💻 **PC Control** — Shutdown, restart, sleep
- 🧠 **Memory** — Remembers past commands and conversations
- 🎨 **Stark HUD** — Iron Man inspired browser interface

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Voice Output | Murf.ai API |
| Voice Input | Web Speech API + SoundDevice |
| AI Brain | Ollama + Gemma3:1b (offline) |
| Backend | Python |
| Frontend | HTML, CSS, JavaScript |
| Communication | WebSocket |
| Automation | PyAutoGUI, PyPerClip |

