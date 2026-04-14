import os
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
import threading
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration ---
MEMORY_FILE    = "memory.json"
MURF_API_KEY   = "ap2_0fca7091-a9f0-4131-9c6b-b6a654bc1063"
MURF_VOICE_ID  = "en-IN-rohan"
AUDIO_PATH     = r"E:\jarvis-claw\murf_output.mp3"

# --- Email config ---
EMAIL_ADDRESS  = "leharinshainsha05@gmail.com"
EMAIL_PASSWORD = "tgkp ofqn iktw xolf"

# --- Speech recognizer ---
recognizer = sr.Recognizer()

# --- TTS fallback engine ---
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 175)
tts_engine.setProperty("volume", 1.0)

# --- Chat history ---
chat_history = []

# --- Overlay reference ---
overlay = None

# =============================================================================
# JARVIS OVERLAY (Siri-like floating window)
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

        self._alpha = 0.0
        self._hide_after_id = None
        self._pulse_state = True

    def _set_alpha(self, val):
        self._alpha = max(0.0, min(1.0, val))
        self.root.attributes("-alpha", self._alpha)

    def show(self, status="LISTENING", cmd="", resp=""):
        if self._hide_after_id:
            self.root.after_cancel(self._hide_after_id)
            self._hide_after_id = None
        self.status_var.set(status)
        self.cmd_var.set(f"▷ {cmd.upper()}" if cmd else "")
        self.resp_var.set(resp)
        self._fade_in()
        self._start_pulse()

    def update(self, status=None, cmd=None, resp=None):
        if status: self.status_var.set(status)
        if cmd is not None: self.cmd_var.set(f"▷ {cmd.upper()}" if cmd else "")
        if resp is not None: self.resp_var.set(resp)

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
        current = self.canvas.itemcget(self.dot, "fill")
        new_color = "#004466" if current == "#00d2ff" else "#00d2ff"
        self.canvas.itemconfig(self.dot, fill=new_color)
        self.root.after(500, self._pulse)

    def run(self):
        self.root.mainloop()


def overlay_show(status="LISTENING", cmd="", resp=""):
    global overlay
    if overlay:
        overlay.root.after(0, lambda: overlay.show(status, cmd, resp))

def overlay_update(status=None, cmd=None, resp=None):
    global overlay
    if overlay:
        overlay.root.after(0, lambda: overlay.update(status, cmd, resp))

def overlay_hide(delay_ms=4000):
    global overlay
    if overlay:
        overlay.root.after(0, lambda: overlay.hide_after(delay_ms))


# =============================================================================
# 1. VOICE
# =============================================================================

def _download_murf(text, path):
    try:
        body = json.dumps({
            "voiceId"    : MURF_VOICE_ID,
            "text"       : text,
            "audioFormat": "MP3"
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.murf.ai/v1/speech/generate",
            data=body,
            headers={
                "Content-Type": "application/json",
                "api-key"     : MURF_API_KEY
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            audio_url = (
                result.get("audioFile") or
                result.get("audio_file") or
                result.get("url") or
                result.get("encodedAudio") or ""
            )
        if audio_url and audio_url.startswith("http"):
            with urllib.request.urlopen(audio_url) as ar:
                with open(path, "wb") as f:
                    f.write(ar.read())
            return True
    except Exception as e:
        print(f"Murf download error: {e}")
    return False

def _play_mp3(path):
    uri = path.replace("\\", "/")
    ps = (
        "Add-Type -AssemblyName presentationCore; "
        "$mp = New-Object System.Windows.Media.MediaPlayer; "
        "$mp.Open([uri]('" + uri + "')); "
        "Start-Sleep -Milliseconds 500; "
        "$mp.Play(); "
        "$i = 0; "
        "while (-not $mp.NaturalDuration.HasTimeSpan -and $i -lt 20) { Start-Sleep -Milliseconds 100; $i++ }; "
        "$secs = [math]::Ceiling($mp.NaturalDuration.TimeSpan.TotalSeconds) + 1; "
        "Start-Sleep -Seconds $secs; "
        "$mp.Stop()"
    )
    subprocess.run(["PowerShell", "-Command", ps], timeout=30)

def speak(text):
    """Speaks using PowerShell TTS — hidden window, no flash."""
    text = text.replace("dude", "Thambii")
    print(f"🎙️ [JARVIS]: {text}")
    overlay_update(status="SPEAKING", resp=text)
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
    sample_rate = 16000
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
            text = recognizer.recognize_google(audio).lower().strip()
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
        audio = sr.AudioData(audio_data.tobytes(), 16000, 2)
        command = recognizer.recognize_google(audio)
        print(f"✅ You said: {command}")
        return command.lower().strip()
    except sr.UnknownValueError:
        speak("I did not catch that Thambii.")
        return ""
    except sr.RequestError:
        speak("Speech service unavailable.")
        return ""
    except Exception as e:
        print(f"Command listen error: {e}")
        return ""

def log_task(task, detail):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry  = {"timestamp": timestamp, "task": task, "detail": detail}
    data = []
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            try:    data = json.load(f)
            except: data = []
    data.append(new_entry)
    with open(MEMORY_FILE, "w") as f:
        json.dump(data[-100:], f, indent=4)

def load_memory_summary():
    if not os.path.exists(MEMORY_FILE):
        return "No past history yet."
    with open(MEMORY_FILE, "r") as f:
        try:    data = json.load(f)
        except: return "No past history yet."
    if not data:
        return "No past history yet."
    lines = []
    for entry in data[-30:]:
        lines.append(f"[{entry['timestamp']}] {entry['task']}: {entry['detail']}")
    return "\n".join(lines)

# =============================================================================
# 2. OLLAMA AI CHAT
# =============================================================================

def ask_ollama(user_input):
    try:
        chat_history.append({"role": "user", "content": user_input})
        memory   = load_memory_summary()
        messages = [
            {
                "role"   : "system",
                "content": (
                    "You are Jarvis, a sophisticated AI assistant. "
                    "You are talking to Thambii, your creator. "
                    "Answer questions directly and factually. "
                    "Keep responses to 1 to 2 sentences max. "
                    "Never use markdown formatting like ** or # or * in your responses. "
                    "Never ask questions back. Never use bullet points.\n\n"
                    + memory
                )
            }
        ] + chat_history

        body = json.dumps({
            "model"   : "gemma3:1b",
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
        if len(chat_history) > 20:
            chat_history.pop(0)
            chat_history.pop(0)
        return reply

    except Exception as e:
        print(f"Ollama error: {e}")
        return "Sorry Thambii, I could not reach my brain right now. Is Ollama running?"

# =============================================================================
# 3. SPOTIFY
# =============================================================================

def play_spotify(query):
    query = query.strip().lower()
    if query in ["liked songs", "liked", "my liked songs", "saved songs"]:
        uri = "spotify:user:leharin:collection"
        speak("Opening your liked songs on Spotify.")
    else:
        encoded = query.replace(" ", "%20")
        uri = f"spotify:search:{encoded}"
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

# =============================================================================
# 4. WHATSAPP HELPERS
# =============================================================================

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
    print(f"Opening WhatsApp for {contact_name}...")
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
    print(f"Searching for {contact_name}...")
    time.sleep(2.5)
    pyautogui.press("down")
    time.sleep(0.5)
    pyautogui.press("enter")
    print("Chat opened.")
    time.sleep(3)
    pyautogui.click(240, 400)
    time.sleep(0.5)

# =============================================================================
# 5. SKILL FUNCTIONS
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
        speak(f"Sorry Thambii, {site_name} is not in my list.")

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

def whatsapp_message(contact_name, message_text):
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
    speak(f"Message sent to {contact_name}, Thambii.")

def whatsapp_call(contact_name, call_type="voice"):
    print(f"Calling {contact_name} on WhatsApp...")
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
    speak(f"{call_type.capitalize()} call started, Thambii.")

def send_email(to_address, subject, body):
    try:
        speak(f"Sending email to {to_address}.")
        msg            = MIMEMultipart()
        msg["From"]    = EMAIL_ADDRESS
        msg["To"]      = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_address, msg.as_string())
        server.quit()
        speak("Email sent successfully, Thambii.")
        log_task("Email", f"To: {to_address} | Subject: {subject}")
    except Exception as e:
        speak("Sorry, I could not send the email.")
        print(f"Email error: {e}")

def set_reminder(message, minutes):
    speak(f"Reminder set for {minutes} minutes from now.")
    log_task("Reminder Set", f"{minutes} min — {message}")
    def _remind():
        time.sleep(minutes * 60)
        speak(f"Reminder: {message}")
        print(f"⏰ REMINDER: {message}")
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
    speak("Shutdown cancelled, Thambii.")

# =============================================================================
# 6. COMMAND HANDLER
# =============================================================================

def handle_command(cmd):
    try:
        if "hey jarvis" in cmd:
            cmd = cmd.replace("hey jarvis", "").strip()

        overlay_update(status="THINKING", cmd=cmd)

        if cmd.startswith("chat "):
            user_input = cmd.replace("chat", "", 1).strip()
            reply = ask_ollama(user_input)
            speak(reply)
            overlay_hide(5000)
            log_task("Chat", f"Q: {user_input} | A: {reply}")
            return

        if not cmd:
            speak("Yes Thambii, how can I help?")
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
                speak("Try: hey jarvis send message to Amma saying I will be late.")
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
                speak("Who should I call, Thambii?")
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
            speak("Going to sleep. Say Hey Jarvis to wake me up.")
            overlay_hide(2000)
            return

        else:
            reply = ask_ollama(cmd)
            speak(reply)
            overlay_hide(5000)
            log_task("Chat", f"Q: {cmd} | A: {reply}")

    except Exception as e:
        print(f"Command error: {e}")
        speak("Something went wrong. Please try again.")
        overlay_hide(3000)

# =============================================================================
# WEBSOCKET SERVER
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
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, process_command_ws, cmd
                    )
                    await ws_broadcast({"type": "response", "text": response})
                    await ws_broadcast({"type": "status", "status": "standby"})
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
        msg = json.dumps(data)
        disconnected = set()
        for client in connected_clients:
            try:
                await client.send(msg)
            except Exception:
                disconnected.add(client)
        connected_clients -= disconnected

def process_command_ws(command):
    try:
        cmd = command.strip()
        if cmd.startswith("hey jarvis"):
            cmd = cmd.replace("hey jarvis", "", 1).strip()
        elif cmd.startswith("chat"):
            cmd = cmd.replace("chat", "", 1).strip()

        if not cmd:
            return "Yes sir, how can I help?"

        if cmd.startswith("play "):
            query = cmd.replace("play", "", 1).strip()
            play_spotify(query)
            return f"Playing {query} on Spotify, sir."

        elif "youtube" in cmd:
            query = cmd.split("youtube", 1)[-1].replace("search", "").replace("for", "").strip()
            open_youtube(query if query else None)
            return f"Opening YouTube{' for ' + query if query else ''}, sir."

        elif "search google for" in cmd:
            query = cmd.split("search google for", 1)[1].strip()
            search_google(query)
            return f"Searching Google for {query}, sir."

        elif "open" in cmd:
            site = cmd.replace("open", "").strip()
            open_website(site)
            return f"Opening {site}, sir."

        elif "time" in cmd:
            t = datetime.now().strftime("%I:%M %p")
            return f"The current time is {t}, sir."

        elif "date" in cmd or "today" in cmd:
            d = datetime.now().strftime("%A, %d %B %Y")
            return f"Today is {d}, sir."

        elif ("send message to" in cmd or "send a message to" in cmd) and "saying" in cmd:
            after_to  = cmd.split("send message to", 1)[1] if "send message to" in cmd else cmd.split("send a message to", 1)[1]
            name_part = after_to.split("saying", 1)[0].strip().title()
            text_part = after_to.split("saying", 1)[1].strip()
            whatsapp_message(name_part, text_part)
            return f"Message sent to {name_part}, sir."

        elif "call" in cmd:
            call_type = "video" if "video" in cmd else "voice"
            name = (cmd.replace("video call","").replace("voice call","")
                    .replace("call","").replace("on whatsapp","").replace("whatsapp","").strip().title())
            name = name.rstrip(".")
            whatsapp_call(name, call_type)
            return f"{call_type.capitalize()} call started with {name}, sir."

        elif "remind me in" in cmd and "minutes to" in cmd:
            after_in = cmd.split("remind me in", 1)[1].strip()
            minutes  = int(after_in.split("minutes to", 1)[0].strip())
            reminder = after_in.split("minutes to", 1)[1].strip()
            set_reminder(reminder, minutes)
            return f"Reminder set for {minutes} minutes, sir."

        elif "shutdown" in cmd or "shut down" in cmd:
            shutdown_pc()
            return "Initiating shutdown sequence, sir."

        elif "restart" in cmd:
            restart_pc()
            return "Restarting systems, sir."

        elif "sleep" in cmd:
            sleep_pc()
            return "Entering sleep mode, sir."

        elif "cancel" in cmd:
            cancel_shutdown()
            return "Shutdown cancelled, sir."

        else:
            reply = ask_ollama(cmd)
            speak(reply)
            return reply

    except Exception as e:
        return f"Error processing command: {str(e)}"

async def start_ws_server():
    async with websockets.serve(ws_handler, "localhost", 8765):
        print("[ WS ] WebSocket server running on ws://localhost:8765")
        await asyncio.Future()

def run_ws_server():
    asyncio.run(start_ws_server())

# =============================================================================
# MAIN
# =============================================================================

def jarvis_loop():
    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()
    print("[ WS ] WebSocket server started on ws://localhost:8765")

    speak("Jarvis is active. Listening for Hey Jarvis.")
    print("=" * 50)
    print("👂 Say 'Hey Jarvis' anytime to wake me up!")
    print("=" * 50)

    while True:
        try:
            wake_detected, inline_cmd = listen_for_wake_word()

            if wake_detected:
                overlay_show(status="LISTENING", cmd=inline_cmd if inline_cmd else "")

                if inline_cmd:
                    speak("Yes Thambii.")
                    threading.Thread(
                        target=handle_command,
                        args=(inline_cmd,),
                        daemon=True
                    ).start()
                else:
                    speak("Yes Thambii.")
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
            speak("Shutting down Jarvis. Goodbye Thambii.")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(1)

def main():
    global overlay
    jarvis_thread = threading.Thread(target=jarvis_loop, daemon=True)
    jarvis_thread.start()
    overlay = JarvisOverlay()
    overlay.run()

if __name__ == "__main__":
    main()