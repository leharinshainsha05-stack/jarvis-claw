# JARVIS — Just A Rather Very Intelligent System

> Built for the Murf.ai Hackathon 2025

## Problem Statement
Current voice assistants like Siri or Alexa are fundamentally limited — they can search the web or set timers, but they cannot execute complex, multi-step workflows on a user's local machine. Switching contexts between apps breaks the user's flow state and slows down productivity.

## Solution
JARVIS is a fully voice-controlled AI desktop assistant that executes real multi-step workflows on your local machine — powered by Murf.ai's natural human voice.

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


