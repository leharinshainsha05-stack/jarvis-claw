"""
brain/general_brain.py
───────────────────────
Jarvis v2.0 — General Brain ("The Genius")

Uses Groq SDK (preferred) → HTTP fallback → Ollama fallback.
Self-Correction Loop: up to 3 retry attempts for code fixes.
"""

from __future__ import annotations
import json
import urllib.request
import urllib.error
from datetime import datetime

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GENIUS_PROMPT = """You are Jarvis, a sophisticated AI assistant and debugging partner.
You are assisting {user_name}, an intelligent developer who values precision.

RULES:
- Be direct and accurate. No fluff.
- Keep responses to 1 to 3 sentences unless complexity demands more.
- Never use markdown — responses are spoken aloud via TTS.
- Never use bullet points, asterisks, or headers.
- For code questions, give the fix and a one-line reason.
- Address the user as {user_name}.

SELF-CORRECTION CONTEXT:
{correction_context}
"""


def _call_groq_sdk(api_key: str, model: str, messages: list, max_tokens: int = 512) -> str | None:
    """Call Groq using the official groq SDK — avoids HTTP 403 issues."""
    try:
        from groq import Groq
        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model      = model,
            messages   = messages,
            max_tokens = max_tokens,
            temperature= 0.7,
        )
        return response.choices[0].message.content.strip()
    except ImportError:
        print("[ General Brain ] groq SDK not installed. Run: pip install groq")
        return None
    except Exception as e:
        print(f"[ General Brain ] Groq SDK error: {e}")
        return None


def _call_groq_http(api_key: str, model: str, messages: list, max_tokens: int = 512) -> str | None:
    """HTTP fallback for Groq."""
    try:
        body = json.dumps({
            "model"      : model,
            "messages"   : messages,
            "max_tokens" : max_tokens,
            "temperature": 0.7,
        }).encode("utf-8")
        req = urllib.request.Request(
            GROQ_API_URL,
            data=body,
            headers={
                "Content-Type" : "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[ General Brain ] Groq HTTP error: {e}")
        return None


def _call_ollama_fallback(model: str, messages: list) -> str | None:
    """Local Ollama fallback when Groq unavailable."""
    try:
        body = json.dumps({
            "model"   : model,
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
            return result["message"]["content"].strip()
    except Exception as e:
        print(f"[ General Brain ] Ollama fallback error: {e}")
        return None


class GeneralBrain:
    """The Genius — cloud-powered, self-correcting."""

    def __init__(self, api_key: str, model: str, user_name: str,
                 fallback_model: str = "gemma3:1b", max_retries: int = 3):
        self.api_key        = api_key
        self.model          = model
        self.fallback_model = fallback_model
        self.user_name      = user_name
        self.max_retries    = max_retries
        self._history: list[dict] = []
        self._correction_attempts = 0

    def _call(self, messages: list) -> str | None:
        """Try Groq SDK → HTTP → Ollama fallback."""
        if self.api_key:
            result = _call_groq_sdk(self.api_key, self.model, messages)
            if result:
                return result
            result = _call_groq_http(self.api_key, self.model, messages)
            if result:
                return result
            print("[ General Brain ] Groq failed — using local Ollama")
        return _call_ollama_fallback(self.fallback_model, messages)

    def attempt_with_correction(self, problem: str, screen_output: str = "") -> str:
        """Self-correction loop — up to max_retries attempts."""
        for attempt in range(1, self.max_retries + 1):
            print(f"[ General Brain ] Self-correction attempt {attempt}/{self.max_retries}")
            correction_ctx = ""
            if attempt > 1:
                correction_ctx = (
                    f"Previous attempt {attempt-1} failed. "
                    f"Screen shows: {screen_output[:200]}. "
                    "Try a completely different approach."
                )
            system = GENIUS_PROMPT.format(
                user_name=self.user_name, correction_context=correction_ctx
            )
            messages  = [
                {"role":"system", "content":system},
                {"role":"user",   "content":f"Attempt {attempt}: {problem}"}
            ]
            response = self._call(messages)
            if response and self._looks_like_solution(response):
                self._correction_attempts = attempt
                return response
            screen_output = response or screen_output

        return (
            f"I have tried {self.max_retries} different approaches, {self.user_name}. "
            f"The issue persists. I recommend we look at this together."
        )

    def _looks_like_solution(self, text: str) -> bool:
        error_indicators = ["error:", "traceback", "exception", "failed", "not found"]
        return not any(ind in text.lower() for ind in error_indicators)

    def chat(self, user_input: str, lang: str = "en", screen_context: str = "") -> str | None:
        system = GENIUS_PROMPT.format(user_name=self.user_name, correction_context="")
        if lang != "en":
            system += f"\n\nIMPORTANT: User is speaking {lang}. Respond in the same language."
        if screen_context:
            system += f"\n\nSCREEN CONTEXT: {screen_context[:500]}"

        if self._is_debug_query(user_input):
            return self.attempt_with_correction(user_input, screen_context)

        self._history.append({"role":"user","content":user_input})
        if len(self._history) > 20:
            self._history = self._history[-20:]
        messages = [{"role":"system","content":system}] + self._history
        response = self._call(messages)
        if response:
            self._history.append({"role":"assistant","content":response})
        return response

    def _is_debug_query(self, text: str) -> bool:
        debug_kw = ["error","exception","traceback","bug","fix","broken","not working","crash","fails","debug"]
        return any(kw in text.lower() for kw in debug_kw)

    def clear_history(self):
        self._history = []