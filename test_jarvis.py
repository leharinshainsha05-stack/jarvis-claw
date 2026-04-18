"""
test_jarvis.py
───────────────
Jarvis v2.0 — Feature Test Suite

Run this BEFORE running main.py to verify everything is working.

Usage:
    python test_jarvis.py

Tests:
  [1] Ollama connection
  [2] Semantic Router
  [3] Personal Brain
  [4] General Brain (Groq)
  [5] ChromaDB memory
  [6] SQLite memory
  [7] Language detector
  [8] Screen Vision
  [9] Morning Brief
  [10] CrewAI Orchestrator
  [11] GitHub Monitor
  [12] Calendar Integration
  [13] Confirmation Gate (skipped — needs mic)
  [14] WebSocket server
"""

import os
import sys
import json
import time
import urllib.request

# ── Colours ──
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

PASS = f"{GREEN}✓ PASS{RESET}"
FAIL = f"{RED}✗ FAIL{RESET}"
SKIP = f"{YELLOW}⚠ SKIP{RESET}"

results = []


def test(name: str, fn):
    print(f"  Testing {name}... ", end="", flush=True)
    try:
        msg = fn()
        print(f"{PASS} — {msg}")
        results.append((name, True, msg))
    except Exception as e:
        print(f"{FAIL} — {e}")
        results.append((name, False, str(e)))


def skip(name: str, reason: str):
    print(f"  Testing {name}... {SKIP} — {reason}")
    results.append((name, None, reason))


print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════╗")
print(f"║     JARVIS v2.0 — FEATURE TEST SUITE    ║")
print(f"╚══════════════════════════════════════════╝{RESET}\n")

# ──────────────────────────────────────────
# [1] OLLAMA
# ──────────────────────────────────────────
print(f"{BOLD}[1] Ollama Connection{RESET}")

def test_ollama():
    req  = urllib.request.Request("http://localhost:11434/api/tags")
    with urllib.request.urlopen(req, timeout=5) as resp:
        data   = json.loads(resp.read())
        models = [m['name'] for m in data.get('models', [])]
        if not models:
            raise Exception("No models found. Run: ollama pull gemma3:1b")
        return f"Models available: {', '.join(models[:3])}"

test("Ollama server", test_ollama)

def test_ollama_chat():
    body = json.dumps({
        "model": "gemma3:1b",
        "messages": [{"role":"user","content":"Say OK in one word."}],
        "stream": False
    }).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body,
                                  headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        reply  = result["message"]["content"].strip()
        return f"Response: '{reply[:30]}'"

test("Ollama chat (gemma3:1b)", test_ollama_chat)

# ──────────────────────────────────────────
# [2] SEMANTIC ROUTER
# ──────────────────────────────────────────
print(f"\n{BOLD}[2] Semantic Router{RESET}")

def test_router_import():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from router.semantic_router import SemanticRouter
    r = SemanticRouter()
    return f"Mode: {r.get_route_info()['mode']}"

def test_router_personal():
    from router.semantic_router import SemanticRouter
    r = SemanticRouter()
    result = r.classify("I feel so lonely today, I don't know what to do")
    if result != "PERSONAL":
        raise Exception(f"Expected PERSONAL, got {result}")
    return f"Correctly classified as PERSONAL"

def test_router_general():
    from router.semantic_router import SemanticRouter
    r = SemanticRouter()
    result = r.classify("Debug this Python error in my code")
    if result != "GENERAL":
        raise Exception(f"Expected GENERAL, got {result}")
    return f"Correctly classified as GENERAL"

test("Router import", test_router_import)
test("Personal route", test_router_personal)
test("General route", test_router_general)

# ──────────────────────────────────────────
# [3] PERSONAL BRAIN
# ──────────────────────────────────────────
print(f"\n{BOLD}[3] Personal Brain{RESET}")

def test_personal_brain():
    from brain.personal_brain import PersonalBrain
    pb = PersonalBrain(model="gemma3:1b", vector_db_path="./chroma_db", user_name="Thambii")
    reply = pb.chat("Hello, just wanted to say hi")
    if not reply:
        raise Exception("Empty response")
    return f"Response: '{reply[:50]}...'"

test("Personal Brain chat", test_personal_brain)

# ──────────────────────────────────────────
# [4] GENERAL BRAIN (GROQ)
# ──────────────────────────────────────────
print(f"\n{BOLD}[4] General Brain (Groq){RESET}")

groq_key = os.environ.get("GROQ_API_KEY", "")
if groq_key:
    def test_groq():
        from brain.general_brain import GeneralBrain
        gb    = GeneralBrain(api_key=groq_key, model="llama3-70b-8192", user_name="Thambii")
        reply = gb.chat("What is 2 + 2? Answer in one sentence.")
        if not reply:
            raise Exception("Empty response from Groq")
        return f"Response: '{reply[:60]}'"
    test("Groq API (Llama 3 70B)", test_groq)
else:
    skip("Groq API", "GROQ_API_KEY not set. Get free key at console.groq.com")

# ──────────────────────────────────────────
# [5] CHROMADB
# ──────────────────────────────────────────
print(f"\n{BOLD}[5] ChromaDB Vector Memory{RESET}")

def test_chromadb():
    import chromadb
    client     = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("test_collection")
    collection.add(documents=["test memory"], ids=["test_001"])
    count = collection.count()
    return f"Collection count: {count}"

test("ChromaDB", test_chromadb)

# ──────────────────────────────────────────
# [6] SQLITE MEMORY
# ──────────────────────────────────────────
print(f"\n{BOLD}[6] SQLite Memory{RESET}")

def test_sqlite():
    from memory.sqlite_memory import SQLiteMemory
    mem = SQLiteMemory("./test_jarvis.db")
    mem.log("Test", "Jarvis v2.0 test run")
    mem.add_deadline("Test Project", "2026-12-31", "Test notes")
    stats = mem.get_summary()
    mem.close()
    os.remove("./test_jarvis.db")
    return f"Tasks: {stats['total_tasks']}, Deadlines: {stats['active_deadlines']}"

test("SQLite memory", test_sqlite)

# ──────────────────────────────────────────
# [7] LANGUAGE DETECTOR
# ──────────────────────────────────────────
print(f"\n{BOLD}[7] Language Detector{RESET}")

def test_lang_english():
    from utils.language_detect import LanguageDetector
    d = LanguageDetector()
    r = d.detect("Hello, how are you today?")
    return f"Detected: {r}"

def test_lang_tamil():
    from utils.language_detect import LanguageDetector
    d = LanguageDetector()
    # Tamil script characters
    r = d.detect("வணக்கம் நான் நலமாக இருக்கிறேன்")
    if r != "ta":
        raise Exception(f"Expected 'ta', got '{r}'")
    return f"Detected Tamil correctly"

test("English detection", test_lang_english)
test("Tamil script detection", test_lang_tamil)

# ──────────────────────────────────────────
# [8] SCREEN VISION
# ──────────────────────────────────────────
print(f"\n{BOLD}[8] Screen Vision{RESET}")

def test_screen_vision():
    from utils.screen_vision import ScreenVision
    sv = ScreenVision()
    screenshot = sv.capture_screenshot()
    if screenshot is None:
        raise Exception("Screenshot returned None")
    return f"Screenshot captured: {len(screenshot)} bytes"

test("Screenshot capture", test_screen_vision)

# ──────────────────────────────────────────
# [9] MORNING BRIEF
# ──────────────────────────────────────────
print(f"\n{BOLD}[9] Morning Brief{RESET}")

def test_morning_brief():
    from agentic.morning_brief import MorningBrief
    mb    = MorningBrief(config={"user_name": "Thambii"})
    brief = mb.generate()
    if not brief or len(brief) < 20:
        raise Exception("Brief too short")
    return f"Brief: '{brief[:70]}...'"

test("Morning Brief generation", test_morning_brief)

# ──────────────────────────────────────────
# [10] CREWAI ORCHESTRATOR
# ──────────────────────────────────────────
print(f"\n{BOLD}[10] CrewAI Orchestrator{RESET}")

def test_crew():
    from agentic.crew_orchestrator import CrewOrchestrator
    crew   = CrewOrchestrator(model="gemma3:1b")
    result = crew.run("Tell me one interesting fact about space in one sentence.")
    if not result or len(result) < 10:
        raise Exception("Crew returned empty result")
    return f"Crew result: '{result[:60]}...'"

test("CrewAI 3-agent pipeline", test_crew)

# ──────────────────────────────────────────
# [11] GITHUB MONITOR
# ──────────────────────────────────────────
print(f"\n{BOLD}[11] GitHub Monitor{RESET}")

github_token = os.environ.get("GITHUB_TOKEN", "")
if github_token:
    def test_github():
        from agentic.github_monitor import GitHubMonitor
        gm    = GitHubMonitor()
        notifs = gm.get_notifications()
        return f"Connected. Notifications: {len(notifs)}"
    test("GitHub Monitor", test_github)
else:
    skip("GitHub Monitor", "GITHUB_TOKEN not set. Set it to enable GitHub monitoring.")

# ──────────────────────────────────────────
# [12] CALENDAR INTEGRATION
# ──────────────────────────────────────────
print(f"\n{BOLD}[12] Calendar Integration{RESET}")

def test_calendar():
    from agentic.calendar_integration import CalendarIntegration
    cal = CalendarIntegration()
    if not cal.is_connected:
        return "Calendar offline (credentials.json not found — optional feature)"
    events = cal.get_today_events()
    return f"Calendar connected. Events today: {len(events)}"

test("Calendar Integration", test_calendar)

# ──────────────────────────────────────────
# [13] CONFIRMATION GATE
# ──────────────────────────────────────────
print(f"\n{BOLD}[13] Confirmation Gate{RESET}")
skip("Confirmation Gate", "Requires microphone — tested automatically when running main.py")

# ──────────────────────────────────────────
# [14] WEBSOCKET
# ──────────────────────────────────────────
print(f"\n{BOLD}[14] WebSocket Server{RESET}")
skip("WebSocket", "Tested by running main.py and opening jarvis-frontend/index.html")

# ──────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────
print(f"\n{BOLD}{CYAN}{'═'*50}")
print(f"  TEST SUMMARY")
print(f"{'═'*50}{RESET}")

passed = sum(1 for _, s, _ in results if s is True)
failed = sum(1 for _, s, _ in results if s is False)
skipped = sum(1 for _, s, _ in results if s is None)

for name, status, msg in results:
    if status is True:
        icon = f"{GREEN}✓{RESET}"
    elif status is False:
        icon = f"{RED}✗{RESET}"
    else:
        icon = f"{YELLOW}⚠{RESET}"
    print(f"  {icon}  {name}")

print(f"\n  {GREEN}{passed} passed{RESET}  |  {RED}{failed} failed{RESET}  |  {YELLOW}{skipped} skipped{RESET}")

if failed == 0:
    print(f"\n{GREEN}{BOLD}  ✓ All systems go. Run: python main.py{RESET}\n")
else:
    print(f"\n{YELLOW}{BOLD}  ⚠ Fix the failed tests above, then run: python main.py{RESET}\n")
    print(f"  Common fixes:")
    print(f"    • Ollama not running  → run: ollama serve")
    print(f"    • Model missing       → run: ollama pull gemma3:1b")
    print(f"    • Missing packages    → run: pip install -r requirements.txt")
    print(f"    • No Groq key         → get free key at console.groq.com\n")