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

# =============================================================================
# 1. MURF.AI VOICE — with instant pyttsx3 + background Murf download
# =============================================================================

def _download_murf(text, path):
    """Downloads Murf.ai audio to path. Runs in background thread."""
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
            print(f"Murf audio_url: {audio_url[:80] if audio_url else 'EMPTY'}")
        if audio_url and audio_url.startswith("http"):
            with urllib.request.urlopen(audio_url) as ar:
                with open(path, "wb") as f:
                    f.write(ar.read())
            return True
    except Exception as e:
        print(f"Murf download error: {e}")
    return False

def _play_mp3(path):
    """Play MP3 using PowerShell MediaPlayer — waits until audio finishes."""
    uri = path.replace("\\", "/")
    ps = (
        "Add-Type -AssemblyName presentationCore; "
        "$mp = New-Object System.Windows.Media.MediaPlayer; "
        "$mp.Open([uri]('" + uri + "')); "
        "Start-Sleep -Milliseconds 500; "
        "$mp.Play(); "
        "$dur = $mp.NaturalDuration; "
        "$i = 0; "
        "while (-not $mp.NaturalDuration.HasTimeSpan -and $i -lt 20) { Start-Sleep -Milliseconds 100; $i++ }; "
        "$secs = [math]::Ceiling($mp.NaturalDuration.TimeSpan.TotalSeconds) + 1; "
        "Start-Sleep -Seconds $secs; "
        "$mp.Stop()"
    )
    subprocess.run(["PowerShell", "-Command", ps], timeout=30)

def speak(text):
    """
    Speaks using Murf.ai voice.
    Strategy: speak with pyttsx3 instantly while downloading Murf audio in background.
    Then play Murf audio after pyttsx3 finishes so the user always hears something fast.
    For hackathon demo: Murf voice plays for every response.
    """
    text = text.replace("dude", "Thambii")
    print(f"🎙️ [JARVIS]: {text}")

    # Start Murf download in background thread immediately
    murf_ready = threading.Event()
    def _bg_download():
        success = _download_murf(text, AUDIO_PATH)
        if success:
            murf_ready.set()
    bg = threading.Thread(target=_bg_download, daemon=True)
    bg.start()

    # Wait up to 4 seconds for Murf to download
    murf_ready.wait(timeout=8)

    if murf_ready.is_set() and os.path.exists(AUDIO_PATH):
        # Murf downloaded in time — play it
        try:
            _play_mp3(AUDIO_PATH)
            return
        except Exception as e:
            print(f"Murf play error: {e}")

    # Fallback: pyttsx3
    print("Using pyttsx3 fallback")
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"TTS error: {e}")

def listen():
    print("\n🎤 Listening... (speak now)")
    try:
        duration    = 6
        sample_rate = 16000
        audio_data  = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
        sd.wait()
        audio   = sr.AudioData(audio_data.tobytes(), sample_rate, 2)
        command = recognizer.recognize_google(audio)
        print(f"✅ You said: {command}")
        return command.lower().strip()
    except sr.UnknownValueError:
        print("⏱️ Could not understand. Type your command:")
        return input("Listening: ").lower().strip()
    except sr.RequestError:
        print("Speech unavailable. Type your command:")
        return input("Listening: ").lower().strip()
    except Exception as e:
        print(f"⚠️ Mic error: {e}. Type your command:")
        return input("Listening: ").lower().strip()

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
                    "You are Jarvis, a smart, friendly and witty AI assistant. "
                    "You are talking to Thambii, your creator. "
                    "Keep responses concise — 2 to 3 sentences max unless asked for detail. "
                    "Be helpful and slightly witty like Tony Stark's Jarvis. "
                    "Never use markdown formatting like ** or # in your responses.\n\n"
                    "Here is Thambii's full history of past commands and conversations:\n"
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
# 3. WHATSAPP HELPERS
# =============================================================================

def _focus_whatsapp():
    # Method 1: AppActivate
    ps = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        "[Microsoft.VisualBasic.Interaction]::AppActivate('WhatsApp')"
    )
    subprocess.run(["PowerShell", "-Command", ps], capture_output=True)
    time.sleep(0.5)
    # Method 2: Click center of screen to ensure WhatsApp gets focus
    # WhatsApp chat area is roughly center of screen on 1920x1080
    pyautogui.click(960, 500)
    time.sleep(0.5)

def _is_whatsapp_running():
    """Check if WhatsApp process is already running."""
    result = subprocess.run(
        ["PowerShell", "-Command", "Get-Process WhatsApp -ErrorAction SilentlyContinue"],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())

def _open_whatsapp_chat(contact_name):
    already_running = _is_whatsapp_running()
    subprocess.Popen(["cmd", "/c", "start", "whatsapp://"])
    print(f"Opening WhatsApp for {contact_name}...")
    # If already running just wait 2s, otherwise wait 7s to fully load
    time.sleep(2 if already_running else 7)
    _focus_whatsapp()
    time.sleep(1)
    # Click search bar directly (calibrated: 370, 191)
    pyautogui.click(370, 191)
    time.sleep(1)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.3)
    pyperclip.copy(contact_name)
    pyautogui.hotkey("ctrl", "v")
    print(f"Searching for {contact_name}...")
    time.sleep(2.5)
    # Open first result
    pyautogui.press("down")
    time.sleep(0.5)
    pyautogui.press("enter")
    print("Chat opened.")
    time.sleep(3)
    _focus_whatsapp()
    time.sleep(0.5)

# =============================================================================
# 4. SKILL FUNCTIONS
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
    # Directly click the message input box (1920x1080 calibrated)
    pyautogui.click(1043, 1146)  # Calibrated message input box
    time.sleep(0.8)
    # Clear any draft
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.3)
    # Paste message
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
    # Click the Call dropdown pill to open it
    pyautogui.click(1644, 103)
    time.sleep(1.5)  # Wait for dropdown to appear
    if call_type == "video":
        pyautogui.click(1604, 286)  # Video button (calibrated)
    else:
        pyautogui.click(1338, 274)  # Voice button (calibrated)
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
# 5. MAIN LOOP
# =============================================================================


# =============================================================================
# WEBSOCKET SERVER — connects frontend to backend
# =============================================================================

connected_clients = set()

async def ws_handler(websocket):
    """Handle incoming WebSocket connections from the frontend."""
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
                    # Send status update to frontend
                    await ws_broadcast({"type": "status", "status": "thinking"})
                    # Process command
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, process_command, cmd
                    )
                    # Send response back to frontend
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
    """Send message to all connected frontend clients."""
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

def process_command(command):
    """
    Process a command from frontend — no prefix needed.
    Strips hey jarvis / chat prefix if present.
    """
    try:
        # Strip prefixes if user typed them
        cmd = command.strip()
        if cmd.startswith("hey jarvis"):
            cmd = cmd.replace("hey jarvis", "", 1).strip()
        elif cmd.startswith("chat"):
            cmd = cmd.replace("chat", "", 1).strip()

        if not cmd:
            return "Yes sir, how can I help?"

        if "youtube" in cmd:
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

        elif "send message to" in cmd and "saying" in cmd:
            after_to  = cmd.split("send message to", 1)[1]
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
            # Send to Ollama for AI response
            reply = ask_ollama(cmd)
            speak(reply)
            return reply

    except Exception as e:
        return f"Error processing command: {str(e)}"

async def start_ws_server():
    """Start WebSocket server on port 8765."""
    async with websockets.serve(ws_handler, "localhost", 8765):
        print("[ WS ] WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # Run forever

def run_ws_server():
    """Run WebSocket server in a separate thread."""
    asyncio.run(start_ws_server())

def main():
    # Start WebSocket server in background thread
    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()
    print("[ WS ] WebSocket server started on ws://localhost:8765")
    speak("Jarvis is active. All systems on standby. Say hey Jarvis for commands or chat to talk to me.")

    while True:
        try:
            command = listen()

            if not command:
                continue

            if command.startswith("hey jarvis"):
                cmd = command.replace("hey jarvis", "").strip()

                if not cmd:
                    speak("Yes Thambii, how can I help?")
                    continue

                if "youtube" in cmd:
                    query = cmd.split("youtube", 1)[-1].replace("search", "").replace("for", "").strip()
                    open_youtube(query if query else None)

                elif "search google for" in cmd:
                    search_google(cmd.split("search google for", 1)[1].strip())

                elif "google" in cmd and "search" in cmd:
                    search_google(cmd.replace("google", "").replace("search", "").strip())

                elif "open" in cmd:
                    open_website(cmd.replace("open", "").strip())

                elif "time" in cmd:
                    tell_time()

                elif "date" in cmd or "today" in cmd:
                    tell_date()

                elif "send message to" in cmd and "saying" in cmd:
                    try:
                        after_to  = cmd.split("send message to", 1)[1]
                        name_part = after_to.split("saying", 1)[0].strip().title()
                        text_part = after_to.split("saying", 1)[1].strip()
                        if name_part and text_part:
                            whatsapp_message(name_part, text_part)
                        else:
                            speak("Please say: send message to name saying your message.")
                    except Exception:
                        speak("Try: hey jarvis send message to Amma saying I will be late.")

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

                elif "email to" in cmd:
                    try:
                        parts   = cmd.split("email to", 1)[1].strip()
                        to_addr = parts.split(" subject ", 1)[0].strip()
                        rest    = parts.split(" subject ", 1)[1]
                        subject = rest.split(" body ", 1)[0].strip()
                        body    = rest.split(" body ", 1)[1].strip()
                        send_email(to_addr, subject, body)
                    except Exception:
                        speak("Try: hey jarvis email to someone@gmail.com subject hello body how are you")

                elif "remind me in" in cmd and "minutes to" in cmd:
                    try:
                        after_in = cmd.split("remind me in", 1)[1].strip()
                        minutes  = int(after_in.split("minutes to", 1)[0].strip())
                        reminder = after_in.split("minutes to", 1)[1].strip()
                        set_reminder(reminder, minutes)
                    except Exception:
                        speak("Try: hey jarvis remind me in 5 minutes to drink water.")

                elif "shutdown" in cmd or "shut down" in cmd:
                    shutdown_pc()

                elif "restart" in cmd:
                    restart_pc()

                elif "sleep" in cmd:
                    sleep_pc()

                elif "cancel" in cmd:
                    cancel_shutdown()

                elif "exit" in cmd or "quit" in cmd or "bye" in cmd:
                    speak("Shutting down Jarvis. Goodbye, Thambii.")
                    break

                else:
                    speak("I did not understand that command Thambii. Try again.")

            elif command.startswith("chat"):
                user_input = command.replace("chat", "", 1).strip()
                if not user_input:
                    speak("What would you like to talk about, Thambii?")
                    continue
                print(f"💬 Asking Ollama: {user_input}")
                reply = ask_ollama(user_input)
                speak(reply)
                log_task("Chat", f"Q: {user_input} | A: {reply}")

            else:
                speak("Say hey Jarvis for commands, or chat to talk to me.")

        except KeyboardInterrupt:
            speak("Interrupted. Shutting down.")
            break
        except Exception as e:
            print(f"Error: {e}")
            speak("Something went wrong. Please try again.")


if __name__ == "__main__":
    main()