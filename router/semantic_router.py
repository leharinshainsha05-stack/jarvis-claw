"""
router/semantic_router.py
─────────────────────────
FIXED: Personal routing now correctly catches emotional inputs.
Added Tamil emotional phrases. Lowered threshold for personal detection.
"""
from __future__ import annotations
import re

PERSONAL_EXAMPLES = [
    # Core emotional statements - these MUST route to personal
    "I am sad", "I feel sad", "I am so sad",
    "I am happy", "I feel happy", "I am excited",
    "I am angry", "I feel angry", "I am frustrated",
    "I am lonely", "I feel lonely",
    "I am stressed", "I feel stressed", "I am anxious",
    "I am depressed", "I feel down",
    "I miss someone", "I miss my friend",
    "I feel lonely today",
    "I am so sad right now",
    "I'm frustrated and don't know what to do",
    "I feel anxious about tomorrow",
    "Tell me something funny",
    "I need to vent",
    "I am really happy today",
    "I'm stressed about my exams",
    "I don't know what to do with my life",
    "We had a breakup", "we broke up",
    "My friend betrayed me",
    "I love someone", "I like someone",
    "My mom is angry at me",
    "I had a fight with my friend",
    "I made a mistake today",
    "I am proud of myself",
    "I feel like I'm not good enough",
    "Why is life so hard",
    "Just wanted to talk",
    "Remember when I told you about",
    "Do you remember what I said",
    "Tell me something about myself",
    # Tamil emotional phrases (transliterated)
    "naan romba sad ah irukken",
    "ennaku theriyala enna pannanum",
    "romba kovam ah irukku",
    "naan happy ah irukken",
    "ennaku lonely ah irukku",
    "vanakam epdi iruka",
    "naan stress ah irukken",
    "friend betrayal pannitanga",
    "naan feel pannuren",
    "ennaku bad ah irukku",
    # Hindi emotional phrases
    "mujhe bahut dukh hai",
    "main bahut khush hoon",
    "main bahut pareshan hoon",
    "mujhe kuch samajh nahi aa raha",
    "main sad hoon",
    "yaar kya baat hai",
    "dil dukhi hai",
    # Conversational personal
    "how are you", "what do you think",
    "tell me a joke", "make me laugh",
    "i need advice", "what should i do",
    "talk to me", "i'm bored",
]

GENERAL_EXAMPLES = [
    "Debug this Python error",
    "What is the capital of France",
    "Order me food from Swiggy",
    "Set a reminder for 5 minutes",
    "Open YouTube",
    "Play music on Spotify",
    "Search Google for something",
    "What time is it",
    "What is the date today",
    "Book a train ticket",
    "How to install Python",
    "Explain machine learning",
    "Write code for me",
    "Fix this bug",
    "What is the weather",
    "Send email to someone",
    "Call someone on WhatsApp",
    "Book an Uber",
    "Order pizza",
]

# Direct keyword triggers for personal — bypasses embedding
PERSONAL_TRIGGERS = [
    "i am sad", "i feel sad", "i'm sad",
    "i am happy", "i feel happy", "i'm happy",
    "i am angry", "i feel angry", "i'm angry",
    "i am lonely", "i feel lonely", "i'm lonely",
    "i am stressed", "i feel stressed",
    "i am anxious", "i feel anxious",
    "i am depressed", "i feel depressed",
    "i am excited", "i feel excited",
    "i miss", "i love", "i hate my",
    "i'm frustrated", "i am frustrated",
    "broke up", "breakup", "break up",
    "betrayed", "betrayal",
    "heartbroken", "heart broken",
    "need to vent", "just wanted to talk",
    "talk to me", "tell me a joke",
    "make me laugh", "i'm bored",
    # Tamil triggers
    "vanakam", "epdi iruka", "romba sad",
    "romba happy", "romba kovam", "romba stress",
    "naan feel", "ennaku", "theriyala",
    # Hindi triggers
    "main sad", "mujhe dukh", "bahut dukh",
    "main khush", "pareshan hoon",
]


class SemanticRouter:
    def __init__(self):
        self._model         = None
        self._personal_proto = None
        self._general_proto  = None
        self._np            = None
        self._use_embeddings = False
        self._try_load_model()

    def _try_load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            self._np    = np
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            personal_vecs = self._model.encode(PERSONAL_EXAMPLES, convert_to_numpy=True)
            general_vecs  = self._model.encode(GENERAL_EXAMPLES,  convert_to_numpy=True)
            self._personal_proto = personal_vecs.mean(axis=0)
            self._general_proto  = general_vecs.mean(axis=0)
            self._use_embeddings = True
            print("[ Router ] ✓ Embedding-based routing active")
        except ImportError:
            print("[ Router ] sentence-transformers not installed — keyword routing")
        except Exception as e:
            print(f"[ Router ] Model load failed: {e} — keyword routing")

    def _cosine_sim(self, a, b) -> float:
        na = self._np.linalg.norm(a)
        nb = self._np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(self._np.dot(a, b) / (na * nb))

    def classify(self, text: str) -> str:
        if not text or len(text.strip()) < 2:
            return "GENERAL"

        text_lower = text.lower().strip()

        # ── Direct trigger check (highest priority) ──────────────────
        for trigger in PERSONAL_TRIGGERS:
            if trigger in text_lower:
                print(f"[ Router ] Direct trigger: '{trigger}' → PERSONAL")
                return "PERSONAL"

        # ── Embedding-based classification ────────────────────────────
        if self._use_embeddings:
            vec          = self._model.encode([text], convert_to_numpy=True)[0]
            personal_sim = self._cosine_sim(vec, self._personal_proto)
            general_sim  = self._cosine_sim(vec, self._general_proto)
            print(f"[ Router ] Embedding: personal={personal_sim:.3f} general={general_sim:.3f}")
            # Lower threshold for personal — catch more emotional inputs
            if personal_sim > 0.35 and personal_sim > general_sim * 0.92:
                return "PERSONAL"
            return "GENERAL"

        # ── Keyword fallback ──────────────────────────────────────────
        personal_kw = ["feel","feeling","felt","sad","happy","angry","upset","lonely",
                        "miss","love","cry","depressed","anxious","stress","scared",
                        "worried","hurt","breakup","relationship","friend","family",
                        "vent","talk to me","boring","bored","don't know what to do"]
        general_kw  = ["open","play","search","find","what is","how do","explain",
                        "debug","error","code","time","date","remind","send","call",
                        "email","youtube","spotify","book","order","buy","install"]
        pl = sum(1 for kw in personal_kw if kw in text_lower)
        gl = sum(1 for kw in general_kw  if kw in text_lower)
        return "PERSONAL" if pl > gl else "GENERAL"

    def get_route_info(self) -> dict:
        return {
            "mode"             : "embedding" if self._use_embeddings else "keyword",
            "personal_examples": len(PERSONAL_EXAMPLES),
            "general_examples" : len(GENERAL_EXAMPLES),
        }