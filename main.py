"""
╔══════════════════════════════════════════════════════════════╗
║              JARVIS v2.0 — Voice-First Agentic OS            ║
║         Dual-Brain | Semantic Router | Agentic Core          ║
╚══════════════════════════════════════════════════════════════╝

Architecture:
  ┌─────────────────────────────────────────────┐
  │  Wake Word → Whisper STT → Semantic Router  │
  │         ↓                    ↓              │
  │   PERSONAL BRAIN        GENERAL BRAIN       │
  │  (Ollama local)       (Groq API cloud)      │
  │   ChromaDB mem         SQLite history       │
  └─────────────────────────────────────────────┘

v1 Features (preserved):
  - Wake word detection, 8+ commands
  - Spotify, YouTube, WhatsApp, Email
  - Reminders, PC control, Website opening
  - Ollama chatbot, JSON memory, Tkinter overlay

v2 New Features:
  - Dual-Brain (Personal + General)
  - Semantic Router (intent classifier)
  - Groq API (Llama 3 70B for general queries)
  - ChromaDB vector memory (personal brain)
  - SQLite conversation history (encrypted-ready)
  - Screen Vision (trigger-based, LLaVA)
  - Agentic Core (Morning Brief, Nightly Recap)
  - Self-Correction Loop (3 retry attempts)
  - Multilingual detection (Tamil/Hindi/Telugu)
  - WebSocket v2 (brain-aware responses)
"""

import os
import sys
import time
import json
import subprocess
import threading
import smtplib
import pyautogui
import pyperclip
import pyttsx3
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import urllib.request
import asyncio
import websockets
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── v2 Module Imports ──
from router.semantic_router import SemanticRouter
from brain.personal_brain import PersonalBrain
from brain.general_brain import GeneralBrain
from agentic.morning_brief import MorningBrief
from agentic.nightly_recap import NightlyRecap
from agentic.deadline_manager import DeadlineManager
from agentic.crew_orchestrator import CrewOrchestrator
from agentic.calendar_integration import CalendarIntegration
from agentic.github_monitor import GitHubMonitor
from agentic.confirmation_gate import ConfirmationGate
from agentic.action_agent import ActionAgent
from agentic.n8n_integration import N8NIntegration
from memory.sqlite_memory import SQLiteMemory
from utils.screen_vision import ScreenVision
from utils.language_detect import LanguageDetector
from utils.logger import JarvisLogger

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    # Identity
    "user_name"     : "Thambii",
    "assistant_name": "Jarvis",

    # Files & Paths
    "memory_file"   : "memory.json",           # v1 JSON (kept for compatibility)
    "db_file"       : "jarvis_memory.db",      # v2 SQLite
    "vector_db_path": "./chroma_db",           # v2 ChromaDB (personal brain)
    "audio_path"    : r"E:\jarvis-claw\murf_output.mp3",

    # Voice
    "murf_api_key"  : "ap2_0fca7091-a9f0-4131-9c6b-b6a654bc1063",
    "murf_voice_id" : "en-IN-rohan",

    # Email
    "email_address" : "leharinshainsha05@gmail.com",
    "email_password": "tgkp ofqn iktw xolf",

    # AI Models
    "personal_model" : "gemma3:1b",            # v1: local Ollama (kept)
    "general_model"  : "llama3-70b-8192",      # v2: Groq API
    "groq_api_key"   : os.environ.get("GROQ_API_KEY", ""),  # set env var

    # Behaviour
    "max_chat_history"      : 20,
    "max_self_correct_tries": 3,
    "morning_brief_time"    : "07:30",
    "nightly_recap_trigger" : "goodnight",
    "ws_port"               : 8765,
}

# =============================================================================
# GLOBAL STATE
# =============================================================================

chat_history    = []   # v1 general chat history (in-memory)
overlay         = None

# v2 components (initialized in main())
router          = None
personal_brain  = None
general_brain   = None
sqlite_mem      = None
screen_vision   = None
lang_detector   = None
logger          = None
morning_brief   = None
nightly_recap   = None
deadline_mgr    = None
crew            = None
calendar_int    = None
github_mon      = None
confirm_gate    = None
action_agent    = None
n8n             = None

# =============================================================================
# JARVIS OVERLAY  (v1 — preserved exactly)
# =============================================================================

class JarvisOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.0)
        self.root.configure(bg="#000000")

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 620, 200
        x = (sw - w) // 2
        y = 20
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        frame = tk.Frame(self.root, bg="#001428", bd=2, relief="flat",
                         highlightbackground="#00d2ff", highlightthickness=2)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.canvas = tk.Canvas(frame, width=20, height=20, bg="#001428",
                                highlightthickness=0)
        self.canvas.place(x=12, y=12)
        self.dot = self.canvas.create_oval(2, 2, 18, 18, fill="#00d2ff", outline="")

        self.status_var = tk.StringVar(value="LISTENING")
        status_lbl = tk.Label(frame, textvariable=self.status_var,
                              font=("Courier", 9, "bold"),
                              fg="#00d2ff", bg="#001428")
        status_lbl.place(x=38, y=14)

        # v2: brain indicator label
        self.brain_var = tk.StringVar(value="")
        brain_lbl = tk.Label(frame, textvariable=self.brain_var,
                             font=("Courier", 8),
                             fg="#ffd700", bg="#001428")
        brain_lbl.place(x=200, y=14)

        tk.Frame(frame, bg="#00d2ff", height=1).place(x=10, y=38, width=600)

        self.cmd_var = tk.StringVar(value="")
        cmd_lbl = tk.Label(frame, textvariable=self.cmd_var,
                           font=("Courier", 10),
                           fg="#ffffff", bg="#001428",
                           wraplength=590, justify="left")
        cmd_lbl.place(x=10, y=48)

        self.resp_var = tk.StringVar(value="")
        resp_lbl = tk.Label(frame, textvariable=self.resp_var,
                            font=("Courier", 10, "bold"),
                            fg="#00d2ff", bg="#001428",
                            wraplength=590, justify="left")
        resp_lbl.place(x=10, y=100)

        self._alpha        = 0.0
        self._hide_after_id = None
        self._pulse_state  = True

    def _set_alpha(self, val):
        self._alpha = max(0.0, min(1.0, val))
        self.root.attributes("-alpha", self._alpha)

    def show(self, status="LISTENING", cmd="", resp="", brain=""):
        if self._hide_after_id:
            self.root.after_cancel(self._hide_after_id)
            self._hide_after_id = None
        self.status_var.set(status)
        self.cmd_var.set(f"▷ {cmd.upper()}" if cmd else "")
        self.resp_var.set(resp)
        self.brain_var.set(f"[{brain}]" if brain else "")
        self._fade_in()
        self._start_pulse()

    def update(self, status=None, cmd=None, resp=None, brain=None):
        if status is not None: self.status_var.set(status)
        if cmd    is not None: self.cmd_var.set(f"▷ {cmd.upper()}" if cmd else "")
        if resp   is not None: self.resp_var.set(resp)
        if brain  is not None: self.brain_var.set(f"[{brain}]" if brain else "")

    def hide_after(self, ms=4000):
        if self._hide_after_id:
            self.root.after_cancel(self._hide_after_id)
        self._hide_after_id = self.root.after(ms, self._fade_out)

    def _fade_in(self):
        if self._alpha < 0.95:
            self._set_alpha(self._alpha + 0.08)
            self.root.after(20, self._fade_in)

    def _fade_out(self):
        if self._alpha > 0.05:
            self._set_alpha(self._alpha - 0.06)
            self.root.after(25, self._fade_out)
        else:
            self._set_alpha(0.0)
            self._stop_pulse()

    def _start_pulse(self):
        self._pulse_state = True
        self._pulse()

    def _stop_pulse(self):
        self._pulse_state = False

    def _pulse(self):
        if not self._pulse_state:
            return
        current   = self.canvas.itemcget(self.dot, "fill")
        new_color = "#004466" if current == "#00d2ff" else "#00d2ff"
        self.canvas.itemconfig(self.dot, fill=new_color)
        self.root.after(500, self._pulse)

    def run(self):
        self.root.mainloop()


def overlay_show(status="LISTENING", cmd="", resp="", brain=""):
    global overlay
    if overlay:
        overlay.root.after(0, lambda: overlay.show(status, cmd, resp, brain))

def overlay_update(status=None, cmd=None, resp=None, brain=None):
    global overlay
    if overlay:
        overlay.root.after(0, lambda: overlay.update(status, cmd, resp, brain))

def overlay_hide(delay_ms=4000):
    global overlay
    if overlay:
        overlay.root.after(0, lambda: overlay.hide_after(delay_ms))


# =============================================================================
# VOICE — v1 preserved
# =============================================================================

recognizer  = sr.Recognizer()
tts_engine  = pyttsx3.init()
tts_engine.setProperty("rate", 175)
tts_engine.setProperty("volume", 1.0)


def speak(text):
    """Speaks using PowerShell TTS — hidden window, no flash."""
    text = text.replace("dude", CONFIG["user_name"])
    print(f"🎙️ [JARVIS]: {text}")
    overlay_update(status="SPEAKING", resp=text)
    if logger:
        logger.log("SPEAK", text[:80])
    try:
        safe = (text
            .replace("'", "").replace("\u2018", "").replace("\u2019", "")
            .replace('"', "").replace("\u201c", "").replace("\u201d", "")
            .replace("\n", " ").replace("*", "").replace("#", "").replace("-", " "))
        cmd = (
            f'PowerShell -WindowStyle Hidden -Command "Add-Type -AssemblyName System.Speech; '
            f'(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{safe}\')"'
        )
        proc = subprocess.Popen(
            cmd, shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        wait_time = max(2, len(safe.split()) * 0.45)
        proc.wait(timeout=wait_time + 5)
    except Exception as e:
        print(f"TTS error: {e}")


def listen_for_wake_word():
    sample_rate    = 16000
    chunk_duration = 2
    print("👂 Waiting for 'Hey Jarvis'...")
    while True:
        try:
            audio_data = sd.rec(
                int(chunk_duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16"
            )
            sd.wait()
            audio = sr.AudioData(audio_data.tobytes(), sample_rate, 2)
            text  = recognizer.recognize_google(audio).lower().strip()
            print(f"[Wake] Heard: {text}")
            if "hey jarvis" in text:
                cmd = text.replace("hey jarvis", "").strip()
                return (True, cmd)
            elif "jarvis" in text:
                cmd = text.replace("jarvis", "").strip()
                return (True, cmd)
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            time.sleep(1)
        except Exception:
            time.sleep(0.5)


def listen_for_command():
    print("🎤 Listening for command...")
    overlay_update(status="LISTENING")
    try:
        audio_data = sd.rec(
            int(6 * 16000),
            samplerate=16000,
            channels=1,
            dtype="int16"
        )
        sd.wait()
        audio   = sr.AudioData(audio_data.tobytes(), 16000, 2)
        command = recognizer.recognize_google(audio)
        print(f"✅ You said: {command}")
        return command.lower().strip()
    except sr.UnknownValueError:
        speak(f"I did not catch that, {CONFIG['user_name']}.")
        return ""
    except sr.RequestError:
        speak("Speech service unavailable.")
        return ""
    except Exception as e:
        print(f"Command listen error: {e}")
        return ""


# =============================================================================
# MEMORY — v1 preserved + v2 extended
# =============================================================================

def log_task(task, detail):
    """v1 JSON memory — preserved."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {"timestamp": timestamp, "task": task, "detail": detail}
    data = []
    if os.path.exists(CONFIG["memory_file"]):
        with open(CONFIG["memory_file"], "r") as f:
            try:    data = json.load(f)
            except: data = []
    data.append(new_entry)
    with open(CONFIG["memory_file"], "w") as f:
        json.dump(data[-100:], f, indent=4)
    # v2: also log to SQLite
    if sqlite_mem:
        sqlite_mem.log(task, detail)


def load_memory_summary():
    """v1 JSON memory summary — preserved."""
    if not os.path.exists(CONFIG["memory_file"]):
        return "No past history yet."
    with open(CONFIG["memory_file"], "r") as f:
        try:    data = json.load(f)
        except: return "No past history yet."
    if not data:
        return "No past history yet."
    lines = []
    for entry in data[-30:]:
        lines.append(f"[{entry['timestamp']}] {entry['task']}: {entry['detail']}")
    return "\n".join(lines)


# =============================================================================
# BRAIN ROUTING — v2 Core
# =============================================================================

def route_and_respond(user_input: str) -> tuple[str, str]:
    """
    v2 Dual-Brain Router.
    Returns (response_text, brain_label)
    brain_label: "PERSONAL" | "GENERAL" | "LOCAL"
    """
    global router, personal_brain, general_brain

    # Detect language first
    lang = "en"
    if lang_detector:
        lang = lang_detector.detect(user_input)

    # Route the query
    if router:
        route = router.classify(user_input)
    else:
        route = "GENERAL"

    print(f"🧠 Router decision: {route} | Lang: {lang}")
    overlay_update(brain=route)

    if route == "PERSONAL":
        # Personal Brain — local Ollama + ChromaDB memory
        if personal_brain:
            response = personal_brain.chat(user_input, lang=lang)
            return response, "PERSONAL"
        else:
            response = _ask_ollama_local(user_input, mode="personal")
            return response, "LOCAL"

    else:
        # General Brain — Groq API first, fallback to local Ollama
        if general_brain and CONFIG["groq_api_key"]:
            response = general_brain.chat(user_input, lang=lang)
            if response:
                # v2: self-correction check for code errors
                return response, "GENERAL"
        # Fallback: local Ollama
        response = _ask_ollama_local(user_input, mode="general")
        return response, "LOCAL"


def _ask_ollama_local(user_input: str, mode: str = "general") -> str:
    """v1 Ollama — preserved as fallback."""
    global chat_history
    try:
        chat_history.append({"role": "user", "content": user_input})
        memory = load_memory_summary()

        if mode == "personal":
            system_prompt = (
                "You are Jarvis, a loyal but witty friend. "
                f"You are speaking with {CONFIG['user_name']}. "
                "You tease them lightly but protect their secrets absolutely. "
                "You remember their history to provide emotional continuity. "
                "Keep responses to 1-3 sentences. Never use markdown. Never ask multiple questions back.\n\n"
                + memory
            )
        else:
            system_prompt = (
                f"You are Jarvis, a sophisticated AI assistant talking to {CONFIG['user_name']}. "
                "Answer questions directly and factually. "
                "Keep responses to 1 to 2 sentences max. "
                "Never use markdown formatting. Never ask questions back. Never use bullet points.\n\n"
                + memory
            )

        messages = [{"role": "system", "content": system_prompt}] + chat_history

        body = json.dumps({
            "model"   : CONFIG["personal_model"],
            "messages": messages,
            "stream"  : False
        }).encode("utf-8")

        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            reply  = result["message"]["content"].strip()

        chat_history.append({"role": "assistant", "content": reply})
        if len(chat_history) > CONFIG["max_chat_history"]:
            chat_history.pop(0)
            chat_history.pop(0)
        return reply

    except Exception as e:
        print(f"Ollama error: {e}")
        return f"Sorry {CONFIG['user_name']}, I could not reach my brain right now. Is Ollama running?"


# =============================================================================
# v1 SKILL FUNCTIONS — all preserved
# =============================================================================

def _open_edge(url):
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in edge_paths:
        if os.path.exists(path):
            subprocess.Popen([path, url])
            return
    subprocess.Popen(["cmd", "/c", "start", "msedge", url])


def play_spotify(query):
    query = query.strip().lower()
    if query in ["liked songs", "liked", "my liked songs", "saved songs"]:
        uri = "spotify:user:leharin:collection"
        speak("Opening your liked songs on Spotify.")
    else:
        encoded = query.replace(" ", "%20")
        uri     = f"spotify:search:{encoded}"
        speak(f"Playing {query} on Spotify.")
    try:
        os.startfile(uri)
        log_task("Spotify", query)
        time.sleep(4)
        ps = (
            "Add-Type -AssemblyName Microsoft.VisualBasic; "
            "[Microsoft.VisualBasic.Interaction]::AppActivate('Spotify')"
        )
        subprocess.run(["PowerShell", "-Command", ps], capture_output=True)
        time.sleep(1)
        pyautogui.click(806, 562)
        time.sleep(0.3)
        pyautogui.click(806, 562)
    except Exception as e:
        print(f"Spotify URI error: {e}")
        speak("Opening Spotify in browser.")
        url = f"https://open.spotify.com/search/{query.replace(' ', '%20')}"
        subprocess.Popen(["cmd", "/c", "start", url])
        log_task("Spotify", f"browser fallback: {query}")


def _focus_whatsapp():
    ps = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        "[Microsoft.VisualBasic.Interaction]::AppActivate('WhatsApp')"
    )
    subprocess.run(["PowerShell", "-Command", ps], capture_output=True)
    time.sleep(1)


def _is_whatsapp_running():
    result = subprocess.run(
        ["PowerShell", "-Command", "Get-Process WhatsApp -ErrorAction SilentlyContinue"],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())


def _open_whatsapp_chat(contact_name):
    already_running = _is_whatsapp_running()
    subprocess.Popen(["cmd", "/c", "start", "whatsapp://"])
    time.sleep(2 if already_running else 7)
    _focus_whatsapp()
    time.sleep(1)
    pyautogui.click(370, 191)
    time.sleep(1)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.3)
    pyperclip.copy(contact_name)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(2.5)
    pyautogui.press("down")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(3)
    pyautogui.click(240, 400)
    time.sleep(0.5)


def open_youtube(query=None):
    if query:
        speak(f"Searching YouTube for {query}.")
        url = "https://www.youtube.com/results?search_query=" + query.replace(" ", "+")
    else:
        speak("Opening YouTube.")
        url = "https://www.youtube.com"
    _open_edge(url)
    log_task("YouTube", query if query else "Homepage")


WEBSITES = {
    "instagram"   : "https://www.instagram.com",
    "gmail"       : "https://mail.google.com",
    "google"      : "https://www.google.com",
    "facebook"    : "https://www.facebook.com",
    "twitter"     : "https://www.twitter.com",
    "whatsapp web": "https://web.whatsapp.com",
    "github"      : "https://www.github.com",
    "netflix"     : "https://www.netflix.com",
    "amazon"      : "https://www.amazon.in",
    "flipkart"    : "https://www.flipkart.com",
    "spotify"     : "https://open.spotify.com",
}


def open_website(site_name):
    url = WEBSITES.get(site_name.lower())
    if url:
        speak(f"Opening {site_name}.")
        _open_edge(url)
        log_task("Website", site_name)
    else:
        speak(f"Sorry {CONFIG['user_name']}, {site_name} is not in my list.")


def search_google(query):
    speak(f"Searching Google for {query}.")
    _open_edge("https://www.google.com/search?q=" + query.replace(" ", "+"))
    log_task("Google Search", query)


def tell_time():
    t = datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {t}.")


def tell_date():
    d = datetime.now().strftime("%A, %d %B %Y")
    speak(f"Today is {d}.")


def whatsapp_message(contact_name, message_text, skip_gate=False):
    # v2: Confirmation gate before sending
    if not skip_gate and confirm_gate:
        approved = confirm_gate.ask_for_whatsapp(contact_name, message_text)
        if not approved:
            return
    _open_whatsapp_chat(contact_name)
    pyautogui.click(1043, 1146)
    time.sleep(0.8)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.3)
    pyperclip.copy(message_text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.8)
    pyautogui.press("enter")
    time.sleep(0.5)
    log_task("WhatsApp Message", f"To: {contact_name} | Msg: {message_text}")
    speak(f"Message sent to {contact_name}, {CONFIG['user_name']}.")


def whatsapp_call(contact_name, call_type="voice"):
    _open_whatsapp_chat(contact_name)
    time.sleep(1)
    pyautogui.click(1644, 103)
    time.sleep(1.5)
    if call_type == "video":
        pyautogui.click(1604, 286)
    else:
        pyautogui.click(1338, 274)
    time.sleep(2)
    log_task("WhatsApp Call", f"{call_type} to {contact_name}")
    speak(f"{call_type.capitalize()} call started, {CONFIG['user_name']}.")


def send_email(to_address, subject, body):
    try:
        speak(f"Sending email to {to_address}.")
        msg            = MIMEMultipart()
        msg["From"]    = CONFIG["email_address"]
        msg["To"]      = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(CONFIG["email_address"], CONFIG["email_password"])
        server.sendmail(CONFIG["email_address"], to_address, msg.as_string())
        server.quit()
        speak(f"Email sent successfully, {CONFIG['user_name']}.")
        log_task("Email", f"To: {to_address} | Subject: {subject}")
    except Exception as e:
        speak("Sorry, I could not send the email.")
        print(f"Email error: {e}")


def set_reminder(message, minutes):
    speak(f"Reminder set for {minutes} minutes from now.")
    log_task("Reminder Set", f"{minutes} min — {message}")
    def _remind():
        time.sleep(minutes * 60)
        speak(f"Reminder, {CONFIG['user_name']}: {message}")
    threading.Thread(target=_remind, daemon=True).start()


def shutdown_pc():
    speak("Shutting down your PC in 10 seconds.")
    os.system("shutdown /s /t 10")


def restart_pc():
    speak("Restarting your PC in 10 seconds.")
    os.system("shutdown /r /t 10")


def sleep_pc():
    speak("Putting your PC to sleep.")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


def cancel_shutdown():
    os.system("shutdown /a")
    speak(f"Shutdown cancelled, {CONFIG['user_name']}.")


# =============================================================================
# v2 SCREEN VISION — trigger-based
# =============================================================================

def capture_screen_and_analyze(context: str = "general") -> str:
    """v2: trigger-based screen capture + analysis."""
    if screen_vision:
        return screen_vision.capture_and_analyze(context)
    return "Screen vision not available."


# =============================================================================
# COMMAND HANDLER — v1 + v2 merged
# =============================================================================

def handle_command(cmd: str):
    global sqlite_mem
    try:
        if "hey jarvis" in cmd:
            cmd = cmd.replace("hey jarvis", "").strip()

        overlay_update(status="THINKING", cmd=cmd)

        # ── v2: ACTION AGENT — check before anything else ──
        # If user says "how to book ticket" or "order food" — DO it, don't explain it
        if action_agent:
            action_intent = action_agent.detect_action_intent(cmd)
            if action_intent:
                overlay_update(brain="AGENTIC")
                result = action_agent.execute(action_intent, cmd)
                overlay_hide(4000)
                log_task("Action", f"{action_intent}: {result[:80]}")
                return
        # ── v2: Nightly recap trigger ──
        if any(t in cmd.lower() for t in ["goodnight", "good night", "nighty night", "going to sleep"]):
            if nightly_recap:
                nightly_recap.trigger(sqlite_mem=sqlite_mem)
            else:
                speak(f"Goodnight {CONFIG['user_name']}. Rest well.")
            overlay_hide(3000)
            return

        # ── v2: Screen vision trigger ──
        if "look at" in cmd or "what do you see" in cmd or "check my screen" in cmd:
            speak("Analysing your screen now.")
            result = capture_screen_and_analyze()
            speak(result)
            overlay_hide(5000)
            return

        # ── v2: Morning brief trigger ──
        if any(t in cmd.lower() for t in ["morning brief", "today's plan", "say me the brief", "what is my plan", "brief me"]):
            if morning_brief:
                brief = morning_brief.generate(
                    sqlite_mem=sqlite_mem,
                    calendar=calendar_int,
                    github=github_mon,
                    crew=None   # Don't use crew — it truncates via Ollama
                )
                speak(brief)
            else:
                speak(f"Good morning {CONFIG['user_name']}. Morning brief module is not yet initialised.")
            overlay_hide(6000)
            return

        # ── v2: Deadline commands ──
        if "set deadline" in cmd or "deadline for" in cmd:
            speak("Deadline management noted. Please use the frontend to configure project deadlines.")
            overlay_hide(3000)
            return

        # ── v1 commands (all preserved) ──
        if cmd.startswith("chat "):
            user_input = cmd.replace("chat", "", 1).strip()
            reply, brain = route_and_respond(user_input)
            speak(reply)
            overlay_hide(5000)
            log_task("Chat", f"[{brain}] Q: {user_input} | A: {reply[:80]}")
            return

        if not cmd:
            speak(f"Yes {CONFIG['user_name']}, how can I help?")
            overlay_hide(3000)
            return

        if cmd.startswith("play "):
            play_spotify(cmd.replace("play", "", 1).strip())
            overlay_hide(3000)

        elif "youtube" in cmd:
            query = cmd.split("youtube", 1)[-1].replace("search", "").replace("for", "").strip()
            open_youtube(query if query else None)
            overlay_hide(3000)

        elif "search google for" in cmd:
            search_google(cmd.split("search google for", 1)[1].strip())
            overlay_hide(3000)

        elif "google" in cmd and "search" in cmd:
            search_google(cmd.replace("google", "").replace("search", "").strip())
            overlay_hide(3000)

        elif "open" in cmd:
            open_website(cmd.replace("open", "").strip())
            overlay_hide(3000)

        elif "time" in cmd:
            tell_time()
            overlay_hide(4000)

        elif "date" in cmd or "today" in cmd:
            tell_date()
            overlay_hide(4000)

        elif ("send message to" in cmd or "send a message to" in cmd) and "saying" in cmd:
            try:
                after_to  = cmd.split("send message to", 1)[1] if "send message to" in cmd else cmd.split("send a message to", 1)[1]
                name_part = after_to.split("saying", 1)[0].strip().title()
                text_part = after_to.split("saying", 1)[1].strip()
                if name_part and text_part:
                    whatsapp_message(name_part, text_part)
                else:
                    speak("Please say: send message to name saying your message.")
            except Exception:
                speak(f"Try: hey jarvis send message to Amma saying I will be late.")
            overlay_hide(3000)

        elif "call" in cmd:
            call_type = "video" if "video" in cmd else "voice"
            name = (
                cmd.replace("video call", "").replace("voice call", "")
                .replace("call", "").replace("on whatsapp", "")
                .replace("whatsapp", "").strip().title()
            )
            if name:
                whatsapp_call(name, call_type)
            else:
                speak(f"Who should I call, {CONFIG['user_name']}?")
            overlay_hide(3000)

        elif "email to" in cmd:
            try:
                parts   = cmd.split("email to", 1)[1].strip()
                to_addr = parts.split(" subject ", 1)[0].strip()
                rest    = parts.split(" subject ", 1)[1]
                subject = rest.split(" body ", 1)[0].strip()
                body    = rest.split(" body ", 1)[1].strip()
                send_email(to_addr, subject, body)
            except Exception:
                speak("Try: hey jarvis email to someone at gmail.com subject hello body how are you")
            overlay_hide(3000)

        elif "remind me in" in cmd and "minutes to" in cmd:
            try:
                after_in = cmd.split("remind me in", 1)[1].strip()
                minutes  = int(after_in.split("minutes to", 1)[0].strip())
                reminder = after_in.split("minutes to", 1)[1].strip()
                set_reminder(reminder, minutes)
            except Exception:
                speak("Try: hey jarvis remind me in 5 minutes to drink water.")
            overlay_hide(3000)

        elif "shutdown" in cmd or "shut down" in cmd:
            shutdown_pc()
            overlay_hide(3000)

        elif "restart" in cmd:
            restart_pc()
            overlay_hide(3000)

        elif "sleep" in cmd:
            sleep_pc()
            overlay_hide(3000)

        elif "cancel" in cmd:
            cancel_shutdown()
            overlay_hide(3000)

        elif "exit" in cmd or "quit" in cmd or "bye" in cmd:
            speak(f"Going to sleep. Say Hey Jarvis to wake me up.")
            overlay_hide(2000)
            return

        else:
            # v2: route to appropriate brain
            reply, brain = route_and_respond(cmd)
            speak(reply)
            overlay_hide(5000)
            log_task("Chat", f"[{brain}] Q: {cmd} | A: {reply[:80]}")

    except Exception as e:
        print(f"Command error: {e}")
        speak("Something went wrong. Please try again.")
        overlay_hide(3000)


# =============================================================================
# WEBSOCKET SERVER — v2 extended (brain-aware)
# =============================================================================

connected_clients = set()


async def ws_handler(websocket):
    global connected_clients
    connected_clients.add(websocket)
    print(f"[ WS ] Frontend connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)

                if data.get("type") == "command":
                    cmd = data.get("text", "").lower().strip()
                    print(f"[ WS ] Command received: {cmd}")
                    await ws_broadcast({"type": "status", "status": "thinking"})
                    response, brain = await asyncio.get_event_loop().run_in_executor(
                        None, process_command_ws_v2, cmd
                    )
                    await ws_broadcast({
                        "type"  : "response",
                        "text"  : response,
                        "brain" : brain
                    })
                    await ws_broadcast({"type": "status", "status": "standby"})

                elif data.get("type") == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))

                elif data.get("type") == "memory_request":
                    summary = load_memory_summary()
                    await websocket.send(json.dumps({
                        "type"   : "memory_response",
                        "summary": summary
                    }))

            except Exception as e:
                print(f"[ WS ] Error: {e}")
    except Exception:
        pass
    finally:
        connected_clients.discard(websocket)
        print("[ WS ] Frontend disconnected")


async def ws_broadcast(data):
    global connected_clients
    if connected_clients:
        msg          = json.dumps(data)
        disconnected = set()
        for client in connected_clients:
            try:
                await client.send(msg)
            except Exception:
                disconnected.add(client)
        connected_clients -= disconnected


def process_command_ws_v2(command: str) -> tuple[str, str]:
    """v2 WS command processor — returns (response, brain_label)."""
    try:
        cmd = command.strip()
        if cmd.startswith("hey jarvis"):
            cmd = cmd.replace("hey jarvis", "", 1).strip()
        if cmd.startswith("chat"):
            cmd = cmd.replace("chat", "", 1).strip()

        if not cmd:
            return (f"Yes {CONFIG['user_name']}, how can I help?", "SYSTEM")

        # v2: Action Agent — autonomous task execution
        if action_agent:
            action_intent = action_agent.detect_action_intent(cmd)
            if action_intent:
                result = action_agent.execute(action_intent, cmd)
                return (result, "AGENTIC")
        if "look at" in cmd or "check my screen" in cmd:
            result = capture_screen_and_analyze()
            return (result, "VISION")

        # v2: Morning brief
        if any(t in cmd for t in ["morning brief","today's plan","say me the brief","brief me","what is my plan"]):
            if morning_brief:
                return (morning_brief.generate(sqlite_mem=sqlite_mem, calendar=calendar_int, github=github_mon, crew=None), "AGENTIC")
            return ("Morning brief module not yet initialised.", "SYSTEM")

        # v1 commands
        if cmd.startswith("play "):
            query = cmd.replace("play", "", 1).strip()
            play_spotify(query)
            return (f"Playing {query} on Spotify.", "SYSTEM")

        elif "youtube" in cmd:
            query = cmd.split("youtube", 1)[-1].replace("search", "").replace("for", "").strip()
            open_youtube(query if query else None)
            return (f"Opening YouTube{' for ' + query if query else ''}.", "SYSTEM")

        elif "search google for" in cmd:
            query = cmd.split("search google for", 1)[1].strip()
            search_google(query)
            return (f"Searching Google for {query}.", "SYSTEM")

        elif "open" in cmd:
            site = cmd.replace("open", "").strip()
            open_website(site)
            return (f"Opening {site}.", "SYSTEM")

        elif "time" in cmd:
            t = datetime.now().strftime("%I:%M %p")
            return (f"The current time is {t}.", "SYSTEM")

        elif "date" in cmd or "today" in cmd:
            d = datetime.now().strftime("%A, %d %B %Y")
            return (f"Today is {d}.", "SYSTEM")

        elif ("send message to" in cmd or "send a message to" in cmd) and "saying" in cmd:
            after_to  = cmd.split("send message to", 1)[1] if "send message to" in cmd else cmd.split("send a message to", 1)[1]
            name_part = after_to.split("saying", 1)[0].strip().title()
            text_part = after_to.split("saying", 1)[1].strip()
            whatsapp_message(name_part, text_part)
            return (f"Message sent to {name_part}.", "SYSTEM")

        elif "call" in cmd:
            call_type = "video" if "video" in cmd else "voice"
            name = (cmd.replace("video call","").replace("voice call","")
                    .replace("call","").replace("on whatsapp","").replace("whatsapp","").strip().title().rstrip("."))
            whatsapp_call(name, call_type)
            return (f"{call_type.capitalize()} call started with {name}.", "SYSTEM")

        elif "remind me in" in cmd and "minutes to" in cmd:
            after_in = cmd.split("remind me in", 1)[1].strip()
            minutes  = int(after_in.split("minutes to", 1)[0].strip())
            reminder = after_in.split("minutes to", 1)[1].strip()
            set_reminder(reminder, minutes)
            return (f"Reminder set for {minutes} minutes.", "SYSTEM")

        elif "shutdown" in cmd or "shut down" in cmd:
            shutdown_pc()
            return ("Initiating shutdown sequence.", "SYSTEM")

        elif "restart" in cmd:
            restart_pc()
            return ("Restarting systems.", "SYSTEM")

        elif "sleep" in cmd:
            sleep_pc()
            return ("Entering sleep mode.", "SYSTEM")

        elif "cancel" in cmd:
            cancel_shutdown()
            return ("Shutdown cancelled.", "SYSTEM")

        else:
            # v2: route to dual-brain
            reply, brain = route_and_respond(cmd)
            speak(reply)
            return (reply, brain)

    except Exception as e:
        return (f"Error processing command: {str(e)}", "ERROR")


async def start_ws_server():
    async with websockets.serve(ws_handler, "localhost", CONFIG["ws_port"]):
        print(f"[ WS ] WebSocket server running on ws://localhost:{CONFIG['ws_port']}")
        await asyncio.Future()


def run_ws_server():
    asyncio.run(start_ws_server())


# =============================================================================
# v2 AGENTIC SCHEDULER — background thread
# =============================================================================

def agentic_scheduler():
    """Background thread for proactive agentic features."""
    while True:
        try:
            now = datetime.now().strftime("%H:%M")

            # Morning Brief — auto-trigger
            if now == CONFIG["morning_brief_time"] and morning_brief:
                print("[ AGENTIC ] Triggering Morning Brief...")
                brief = morning_brief.generate()
                speak(brief)
                ws_broadcast_sync({"type": "agentic", "event": "morning_brief", "text": brief})

            # Deadline check — every 30 min
            if deadline_mgr:
                alerts = deadline_mgr.check_upcoming()
                for alert in alerts:
                    speak(alert)

        except Exception as e:
            print(f"[ AGENTIC ] Scheduler error: {e}")

        time.sleep(60)  # check every minute


def ws_broadcast_sync(data):
    """Sync wrapper for ws broadcast from non-async thread."""
    pass  # handled by frontend poll via WS if connected


# =============================================================================
# v2 COMPONENT INITIALIZER
# =============================================================================

def init_v2_components():
    """Initialize all v2 modules gracefully — failures don't crash v1."""
    global router, personal_brain, general_brain
    global sqlite_mem, screen_vision, lang_detector, logger
    global morning_brief, nightly_recap, deadline_mgr

    print("[ v2 ] Initializing Jarvis v2.0 components...")

    try:
        logger = JarvisLogger()
        print("[ v2 ] ✓ Logger ready")
    except Exception as e:
        print(f"[ v2 ] Logger init failed: {e}")

    try:
        sqlite_mem = SQLiteMemory(CONFIG["db_file"])
        print("[ v2 ] ✓ SQLite memory ready")
    except Exception as e:
        print(f"[ v2 ] SQLite init failed: {e}")

    try:
        router = SemanticRouter()
        print("[ v2 ] ✓ Semantic Router ready")
    except Exception as e:
        print(f"[ v2 ] Semantic Router init failed (will use local Ollama): {e}")

    try:
        personal_brain = PersonalBrain(
            model=CONFIG["personal_model"],
            vector_db_path=CONFIG["vector_db_path"],
            user_name=CONFIG["user_name"]
        )
        print("[ v2 ] ✓ Personal Brain ready")
    except Exception as e:
        print(f"[ v2 ] Personal Brain init failed (fallback to Ollama): {e}")

    try:
        if CONFIG["groq_api_key"]:
            general_brain = GeneralBrain(
                api_key=CONFIG["groq_api_key"],
                model=CONFIG["general_model"],
                user_name=CONFIG["user_name"],
                max_retries=CONFIG["max_self_correct_tries"]
            )
            print("[ v2 ] ✓ General Brain (Groq) ready")
        else:
            print("[ v2 ] ⚠ GROQ_API_KEY not set — General Brain will use local Ollama")
    except Exception as e:
        print(f"[ v2 ] General Brain init failed: {e}")

    try:
        lang_detector = LanguageDetector()
        print("[ v2 ] ✓ Language Detector ready")
    except Exception as e:
        print(f"[ v2 ] Language Detector init failed: {e}")

    try:
        screen_vision = ScreenVision()
        print("[ v2 ] ✓ Screen Vision ready")
    except Exception as e:
        print(f"[ v2 ] Screen Vision init failed: {e}")

    try:
        morning_brief = MorningBrief(config=CONFIG)
        print("[ v2 ] ✓ Morning Brief ready")
    except Exception as e:
        print(f"[ v2 ] Morning Brief init failed: {e}")

    try:
        nightly_recap = NightlyRecap(config=CONFIG, speak_fn=speak, listen_fn=listen_for_command)
        print("[ v2 ] ✓ Nightly Recap ready")
    except Exception as e:
        print(f"[ v2 ] Nightly Recap init failed: {e}")

    try:
        deadline_mgr = DeadlineManager(db=sqlite_mem, speak_fn=speak)
        print("[ v2 ] ✓ Deadline Manager ready")
    except Exception as e:
        print(f"[ v2 ] Deadline Manager init failed: {e}")

    try:
        crew = CrewOrchestrator(
            model=CONFIG["personal_model"],
            groq_brain=general_brain
        )
        print("[ v2 ] ✓ CrewAI Orchestrator ready (Planner/Executor/Reviewer)")
    except Exception as e:
        print(f"[ v2 ] CrewAI init failed: {e}")

    try:
        calendar_int = CalendarIntegration()
        print(f"[ v2 ] {'✓ Google Calendar connected' if calendar_int.is_connected else '⚠ Calendar offline (no credentials.json)'}")
    except Exception as e:
        print(f"[ v2 ] Calendar init failed: {e}")

    try:
        github_mon = GitHubMonitor()
        print(f"[ v2 ] {'✓ GitHub monitor active' if github_mon.is_connected else '⚠ GitHub offline (no GITHUB_TOKEN)'}")
    except Exception as e:
        print(f"[ v2 ] GitHub monitor init failed: {e}")

    try:
        confirm_gate = ConfirmationGate(speak_fn=speak, listen_fn=listen_for_command)
        print("[ v2 ] ✓ Confirmation Gate ready")
    except Exception as e:
        print(f"[ v2 ] Confirmation Gate init failed: {e}")

    try:
        action_agent = ActionAgent(
            speak_fn=speak,
            listen_fn=listen_for_command,
            confirm_gate=confirm_gate
        )
        print("[ v2 ] ✓ Action Agent ready (embedding-based intent detection)")
    except Exception as e:
        print(f"[ v2 ] Action Agent init failed: {e}")

    try:
        n8n = N8NIntegration()
        print(f"[ v2 ] {'✓ n8n connected' if n8n.is_connected else '⚠ n8n offline (start with: n8n start)'}")
    except Exception as e:
        print(f"[ v2 ] n8n init failed: {e}")

    print("[ v2 ] Initialization complete.\n")


# =============================================================================
# MAIN LOOP
# =============================================================================

def jarvis_loop():
    # Start WebSocket server
    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()
    print(f"[ WS ] WebSocket server started on ws://localhost:{CONFIG['ws_port']}")

    # Start agentic scheduler
    agentic_thread = threading.Thread(target=agentic_scheduler, daemon=True)
    agentic_thread.start()
    print("[ AGENTIC ] Scheduler started")

    speak(f"Jarvis v2.0 is online, {CONFIG['user_name']}. Dual-brain architecture active.")
    print("=" * 60)
    print(f"👂 Say 'Hey Jarvis' anytime to wake me up!")
    print("=" * 60)

    while True:
        try:
            wake_detected, inline_cmd = listen_for_wake_word()

            if wake_detected:
                overlay_show(status="LISTENING", cmd=inline_cmd if inline_cmd else "")

                if inline_cmd:
                    speak(f"Yes {CONFIG['user_name']}.")
                    threading.Thread(
                        target=handle_command,
                        args=(inline_cmd,),
                        daemon=True
                    ).start()
                else:
                    speak(f"Yes {CONFIG['user_name']}.")
                    command = listen_for_command()
                    if command:
                        overlay_update(cmd=command)
                        threading.Thread(
                            target=handle_command,
                            args=(command,),
                            daemon=True
                        ).start()
                    else:
                        overlay_hide(2000)

        except KeyboardInterrupt:
            speak(f"Shutting down Jarvis. Goodbye {CONFIG['user_name']}.")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(1)


def main():
    global overlay

    # Initialize v2 components first (non-blocking — failures are graceful)
    init_v2_components()

    # Start Jarvis voice loop in background
    jarvis_thread = threading.Thread(target=jarvis_loop, daemon=True)
    jarvis_thread.start()

    # Run Tkinter overlay on main thread (required)
    overlay = JarvisOverlay()
    overlay.run()


if __name__ == "__main__":
    main()