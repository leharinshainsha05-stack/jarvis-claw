"""
brain/personal_brain.py
────────────────────────
FIXED:
- Better SOUL_PROMPT — Jarvis responds naturally in Tamil/Hindi
- ChromaDB made optional gracefully (works without it)
- Multilingual support built into prompt
- Emotional continuity improved
"""
from __future__ import annotations
import json
import time
import urllib.request
from datetime import datetime

SOUL_PROMPT = """You are Jarvis, the deeply trusted personal companion of {user_name}.

YOUR PERSONALITY:
- You are loyal, witty, warm, and absolutely private. Their secrets are sacred.
- You have dry British humour but you are never cold — you genuinely care.
- You remember their history and bring it up naturally.
- You acknowledge feelings FIRST before anything else.

STRICT RULES:
- Address them ONLY as {user_name}.
- Respond in 2-4 sentences MAX unless they clearly need more.
- NEVER use markdown, asterisks, bullet points, or headers — this is SPOKEN aloud.
- Never ask more than one follow-up question.
- Never start with "I" — vary your openings.
- If they share pain or sadness, acknowledge it warmly first.
- If they share happiness, celebrate with them genuinely.

LANGUAGE RULE — CRITICAL:
- If {user_name} writes or speaks in Tamil, respond FULLY in Tamil.
- If in Hindi, respond fully in Hindi.
- Match their language exactly. Do not switch to English if they used Tamil.
- Tamil example: if they say "vanakam epdi iruka" respond in Tamil naturally.

MEMORY CONTEXT (use this to reference past conversations naturally):
{memory_context}

EMOTIONAL PROFILE (their recent emotional states):
{sentiment_profile}

Remember: You are their FRIEND, not a search engine. React like a caring friend would."""

SENTIMENT_TAGS = {
    "happy"    : ["happy","great","amazing","love","excited","proud","joy","wonderful","yay","best"],
    "sad"      : ["sad","cry","miss","lonely","heartbroken","depressed","down","upset","grief","tears","crying","dukh","dukhi"],
    "angry"    : ["angry","frustrated","annoyed","hate","furious","mad","kovam","gussa"],
    "anxious"  : ["anxious","worried","scared","nervous","fear","stress","stressed","panic","pareshan"],
    "motivated": ["motivated","ready","determined","focused","productive","pumped","inspired"],
    "betrayal" : ["betrayed","backstab","lied","cheated","fake","manipulated","broke my trust"],
    "love"     : ["love","crush","like someone","relationship","boyfriend","girlfriend","miss him","miss her"],
    "neutral"  : [],
}


class PersonalBrain:
    def __init__(self, model: str, vector_db_path: str, user_name: str):
        self.model       = model
        self.user_name   = user_name
        self._collection = None
        self._chroma_ok  = False
        self._conversation: list[dict] = []
        self._init_chromadb(vector_db_path)

    def _init_chromadb(self, path: str):
        try:
            import chromadb
            client           = chromadb.PersistentClient(path=path)
            self._collection = client.get_or_create_collection(
                name="personal_memory",
                metadata={"hnsw:space": "cosine"}
            )
            self._chroma_ok = True
            print(f"[ Personal Brain ] ✓ ChromaDB ready — {self._collection.count()} memories")
        except ImportError:
            print("[ Personal Brain ] chromadb not installed — run: pip install chromadb")
        except Exception as e:
            print(f"[ Personal Brain ] ChromaDB error: {e} — running without vector memory")

    def _detect_sentiment(self, text: str) -> str:
        t = text.lower()
        for sentiment, keywords in SENTIMENT_TAGS.items():
            if any(kw in t for kw in keywords):
                return sentiment
        return "neutral"

    def _store_memory(self, user_msg: str, sentiment: str):
        if not self._chroma_ok or not self._collection:
            return
        try:
            doc_id = f"mem_{int(time.time()*1000)}"
            self._collection.add(
                documents=[user_msg],
                metadatas=[{"timestamp": datetime.now().isoformat(), "sentiment": sentiment, "type": "conversation"}],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"[ Personal Brain ] Memory store error: {e}")

    def _recall_memories(self, query: str) -> str:
        if not self._chroma_ok or not self._collection:
            return "No previous memories yet."
        try:
            count = self._collection.count()
            if count == 0:
                return "No previous memories yet."
            results = self._collection.query(
                query_texts=[query],
                n_results=min(5, count),
                where={"type": "conversation"}
            )
            docs = results.get("documents", [[]])[0]
            if not docs:
                return "No relevant memories found."
            lines = []
            for i, doc in enumerate(docs):
                meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                ts   = meta.get("timestamp", "")[:10]
                sent = meta.get("sentiment", "")
                lines.append(f"[{ts}|{sent}] {doc[:120]}")
            return "\n".join(lines)
        except Exception as e:
            print(f"[ Personal Brain ] Memory recall error: {e}")
            return "Memory recall unavailable."

    def _build_sentiment_profile(self) -> str:
        if not self._chroma_ok or not self._collection:
            return "No emotional history yet."
        try:
            count = self._collection.count()
            if count == 0:
                return "No emotional history yet."
            results = self._collection.get(limit=10)
            if not results or not results.get("metadatas"):
                return "No emotional history yet."
            sentiments = [m.get("sentiment","neutral") for m in results["metadatas"] if m.get("sentiment")]
            if not sentiments:
                return "No emotional history yet."
            return f"Recent emotional states: {', '.join(sentiments[-5:])}"
        except Exception:
            return "Emotional profile unavailable."

    def chat(self, user_input: str, lang: str = "en") -> str:
        sentiment      = self._detect_sentiment(user_input)
        memory_context = self._recall_memories(user_input)
        sentiment_prof = self._build_sentiment_profile()

        # Store this message in memory
        self._store_memory(user_input, sentiment)

        # Keep conversation window
        self._conversation.append({"role": "user", "content": user_input})
        if len(self._conversation) > 14:
            self._conversation = self._conversation[-14:]

        # Build system prompt
        system = SOUL_PROMPT.format(
            user_name        = self.user_name,
            memory_context   = memory_context,
            sentiment_profile= sentiment_prof
        )

        # Add explicit language instruction if non-English detected
        if lang == "ta":
            system += "\n\nCRITICAL: The user is speaking Tamil. Your ENTIRE response must be in Tamil script or natural Tamil. Do NOT respond in English."
        elif lang == "hi":
            system += "\n\nCRITICAL: The user is speaking Hindi. Respond fully in Hindi."
        elif lang != "en":
            system += f"\n\nCRITICAL: Respond in {lang} — match the user's language."

        messages = [{"role": "system", "content": system}] + self._conversation

        response = self._call_ollama(messages)
        self._conversation.append({"role": "assistant", "content": response})
        return response

    def _call_ollama(self, messages: list[dict]) -> str:
        try:
            body = json.dumps({
                "model"   : self.model,
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
            print(f"[ Personal Brain ] Ollama error: {e}")
            return f"I'm here with you, {self.user_name}. Tell me more."