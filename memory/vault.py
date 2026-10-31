"""
memory/vault.py
────────────────
JARVIS Vault MVP — Local Financial Allocation & Spending Protection Module

Core Rules:
1. All amounts stored and computed internally in integer PAISE (1 INR = 100 paise).
2. Pure deterministic Python calculation — NO LLM is used for financial math.
3. Thread-safe execution with transaction atomicity.
4. Fail-closed: invalid requests, negative amounts, or balance overruns return BLOCK.
5. Auditable logging of all ALLOW and BLOCK decisions.
"""

from __future__ import annotations
import sqlite3
import threading
import uuid
from datetime import datetime
from typing import Optional


class JarvisVault:
    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.db_path = db_path
        self._lock    = threading.RLock()
        self._conn    = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        with self._lock, self._conn:
            c = self._conn.cursor()
            # Incoming funds
            c.execute("""
                CREATE TABLE IF NOT EXISTS vault_funds (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp    TEXT NOT NULL,
                    amount_paise INTEGER NOT NULL,
                    source       TEXT NOT NULL,
                    verified     INTEGER DEFAULT 0,
                    notes        TEXT
                )
            """)
            # Category allocations
            c.execute("""
                CREATE TABLE IF NOT EXISTS vault_allocations (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    category        TEXT UNIQUE NOT NULL,
                    allocated_paise INTEGER NOT NULL,
                    status          TEXT NOT NULL,
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    notes           TEXT
                )
            """)
            # Transaction audit log (ALLOW and BLOCK decisions)
            c.execute("""
                CREATE TABLE IF NOT EXISTS vault_transactions (
                    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                    tx_id                  TEXT UNIQUE NOT NULL,
                    timestamp              TEXT NOT NULL,
                    merchant               TEXT NOT NULL,
                    category               TEXT,
                    amount_paise           INTEGER NOT NULL,
                    decision               TEXT NOT NULL,
                    reason                 TEXT NOT NULL,
                    balance_before_paise   INTEGER NOT NULL,
                    spendable_before_paise INTEGER NOT NULL,
                    balance_after_paise    INTEGER NOT NULL,
                    spendable_after_paise  INTEGER NOT NULL,
                    metadata               TEXT
                )
            """)

    @staticmethod
    def rupees_to_paise(amount_rupees: float | int) -> int:
        if not isinstance(amount_rupees, (int, float)):
            raise ValueError("Amount must be a numeric value")
        if amount_rupees <= 0:
            raise ValueError("Amount must be strictly positive")
        return int(round(amount_rupees * 100))

    @staticmethod
    def paise_to_rupees(amount_paise: int) -> float:
        return amount_paise / 100.0

    # ── 1. Record Incoming Funds ──────────────────────────────────────────

    def deposit(self, amount_rupees: float | int, source: str = "user_declared",
                notes: str = "", verified: bool = False) -> dict:
        """
        Record incoming funds (e.g. salary, freelance, user declaration).
        """
        with self._lock:
            paise = self.rupees_to_paise(amount_rupees)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with self._conn:
                self._conn.execute(
                    "INSERT INTO vault_funds (timestamp, amount_paise, source, verified, notes) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (now, paise, source.strip().lower(), 1 if verified else 0, notes.strip())
                )

            summary = self.get_balance_summary()
            return {
                "success"              : True,
                "deposited_rupees"     : amount_rupees,
                "deposited_paise"      : paise,
                "source"               : source,
                "verified"             : verified,
                "total_funds_rupees"   : summary["total_funds_rupees"],
                "safe_to_spend_rupees" : summary["safe_to_spend_rupees"],
                "timestamp"            : now
            }

    # ── 2. Category Allocations ───────────────────────────────────────────

    def allocate(self, category: str, amount_rupees: float | int, status: str = "locked",
                 notes: str = "", allow_update: bool = False) -> dict:
        """
        Allocate money to a category (e.g., parents, rent, groceries).
        status: 'locked' (strictly protected) or 'earmarked' (designated).
        """
        with self._lock:
            cat = category.strip().lower()
            if not cat:
                raise ValueError("Category name cannot be empty")
            status = status.strip().lower()
            if status not in ("locked", "earmarked"):
                raise ValueError("Status must be either 'locked' or 'earmarked'")

            new_paise = self.rupees_to_paise(amount_rupees)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            summary = self.get_balance_summary()
            total_funds = summary["total_funds_paise"]

            # Calculate total allocated excluding existing allocation for this category
            cursor = self._conn.cursor()
            existing = cursor.execute(
                "SELECT allocated_paise, status FROM vault_allocations WHERE category = ?",
                (cat,)
            ).fetchone()

            if existing and not allow_update:
                raise ValueError(
                    f"Allocation for '{cat}' already exists (₹{self.paise_to_rupees(existing[0]):,.2f}, {existing[1]}). "
                    "Use allow_update=True to explicitly update."
                )

            other_allocations = cursor.execute(
                "SELECT COALESCE(SUM(allocated_paise), 0) FROM vault_allocations WHERE category != ?",
                (cat,)
            ).fetchone()[0]

            if other_allocations + new_paise > total_funds:
                available_to_allocate = max(0, total_funds - other_allocations)
                raise ValueError(
                    f"Cannot allocate ₹{amount_rupees:,.2f} to '{cat}'. "
                    f"Exceeds available funds. Maximum unallocated: ₹{self.paise_to_rupees(available_to_allocate):,.2f}."
                )

            with self._conn:
                if existing:
                    self._conn.execute(
                        "UPDATE vault_allocations SET allocated_paise = ?, status = ?, updated_at = ?, notes = ? "
                        "WHERE category = ?",
                        (new_paise, status, now, notes.strip(), cat)
                    )
                else:
                    self._conn.execute(
                        "INSERT INTO vault_allocations (category, allocated_paise, status, created_at, updated_at, notes) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (cat, new_paise, status, now, now, notes.strip())
                    )

            updated_summary = self.get_balance_summary()
            return {
                "success"              : True,
                "category"             : cat,
                "allocated_rupees"     : amount_rupees,
                "status"               : status,
                "safe_to_spend_rupees" : updated_summary["safe_to_spend_rupees"],
                "total_allocated_rupees": updated_summary["total_allocated_rupees"],
                "timestamp"            : now
            }

    # ── 3. Balance & Safe-to-Spend Computation ────────────────────────────

    def get_balance_summary(self) -> dict:
        """
        Compute total funds, total allocations, and remaining spendable balance.
        """
        with self._lock:
            c = self._conn.cursor()

            # Total deposits
            total_deposited = c.execute(
                "SELECT COALESCE(SUM(amount_paise), 0) FROM vault_funds"
            ).fetchone()[0]

            # Total approved spends
            total_spent = c.execute(
                "SELECT COALESCE(SUM(amount_paise), 0) FROM vault_transactions WHERE decision = 'ALLOW'"
            ).fetchone()[0]

            total_funds_paise = max(0, total_deposited - total_spent)

            # Allocations
            alloc_rows = c.execute(
                "SELECT category, allocated_paise, status, notes FROM vault_allocations ORDER BY category"
            ).fetchall()

            locked_paise = 0
            earmarked_paise = 0
            allocations_list = []

            for row in alloc_rows:
                cat, p_amt, stat, notes = row
                if stat == "locked":
                    locked_paise += p_amt
                else:
                    earmarked_paise += p_amt
                allocations_list.append({
                    "category"        : cat,
                    "amount_paise"    : p_amt,
                    "amount_rupees"   : self.paise_to_rupees(p_amt),
                    "status"          : stat,
                    "notes"           : notes or ""
                })

            total_allocated_paise = locked_paise + earmarked_paise
            safe_to_spend_paise = max(0, total_funds_paise - total_allocated_paise)

            return {
                "total_funds_paise"      : total_funds_paise,
                "total_funds_rupees"     : self.paise_to_rupees(total_funds_paise),
                "total_allocated_paise"  : total_allocated_paise,
                "total_allocated_rupees" : self.paise_to_rupees(total_allocated_paise),
                "locked_paise"           : locked_paise,
                "locked_rupees"          : self.paise_to_rupees(locked_paise),
                "earmarked_paise"        : earmarked_paise,
                "earmarked_rupees"       : self.paise_to_rupees(earmarked_paise),
                "safe_to_spend_paise"    : safe_to_spend_paise,
                "safe_to_spend_rupees"   : self.paise_to_rupees(safe_to_spend_paise),
                "allocations"            : allocations_list
            }

    # ── 4. Spending Protection Gatekeeper ─────────────────────────────────

    def evaluate_spending(self, amount_rupees: float | int, merchant: str,
                          category: str = "", tx_id: Optional[str] = None) -> dict:
        """
        Evaluate a spending attempt against safe-to-spend balance.
        Returns explicit 'ALLOW' or 'BLOCK' with auditable log.
        """
        with self._lock:
            # 1. Validation & Input Sanitization
            merchant = (merchant or "Unknown").strip()
            category = (category or "").strip().lower()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tx_id = (tx_id or f"tx_{uuid.uuid4().hex[:12]}").strip()

            c = self._conn.cursor()

            # Check for duplicate transaction id
            dup = c.execute(
                "SELECT id, decision FROM vault_transactions WHERE tx_id = ?",
                (tx_id,)
            ).fetchone()
            if dup:
                return {
                    "decision"            : "BLOCK",
                    "allowed"             : False,
                    "tx_id"               : tx_id,
                    "reason"              : f"Duplicate transaction ID '{tx_id}'. Request rejected for safety.",
                    "amount_rupees"       : amount_rupees,
                    "safe_to_spend_rupees": 0.0,
                    "timestamp"           : now
                }

            # Validate amount
            try:
                paise = self.rupees_to_paise(amount_rupees)
            except Exception as e:
                return {
                    "decision"            : "BLOCK",
                    "allowed"             : False,
                    "tx_id"               : tx_id,
                    "reason"              : f"Invalid spending amount: {str(e)}",
                    "amount_rupees"       : amount_rupees,
                    "safe_to_spend_rupees": 0.0,
                    "timestamp"           : now
                }

            summary_before = self.get_balance_summary()
            total_funds_before = summary_before["total_funds_paise"]
            safe_spend_before  = summary_before["safe_to_spend_paise"]

            # 2. Gate Decision Logic
            if paise > safe_spend_before:
                decision = "BLOCK"
                reason = (
                    f"Attempted spending of ₹{amount_rupees:,.2f} on {merchant} exceeds safe-to-spend balance "
                    f"of ₹{self.paise_to_rupees(safe_spend_before):,.2f}. Protected allocations are locked."
                )
                total_funds_after = total_funds_before
                safe_spend_after  = safe_spend_before
            else:
                decision = "ALLOW"
                reason = (
                    f"Spending of ₹{amount_rupees:,.2f} on {merchant} approved. "
                    f"Remaining safe-to-spend: ₹{self.paise_to_rupees(safe_spend_before - paise):,.2f}."
                )
                total_funds_after = total_funds_before - paise
                safe_spend_after  = safe_spend_before - paise

            # 3. Transaction Persistence
            with self._conn:
                self._conn.execute("""
                    INSERT INTO vault_transactions (
                        tx_id, timestamp, merchant, category, amount_paise,
                        decision, reason, balance_before_paise, spendable_before_paise,
                        balance_after_paise, spendable_after_paise
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tx_id, now, merchant, category, paise, decision, reason,
                    total_funds_before, safe_spend_before, total_funds_after, safe_spend_after
                ))

            return {
                "decision"               : decision,
                "allowed"                : (decision == "ALLOW"),
                "tx_id"                  : tx_id,
                "merchant"               : merchant,
                "amount_rupees"          : amount_rupees,
                "amount_paise"           : paise,
                "safe_to_spend_rupees"   : self.paise_to_rupees(safe_spend_after),
                "reason"                 : reason,
                "timestamp"              : now
            }

    # ── 5. Auditable History ──────────────────────────────────────────────

    def get_transactions(self, limit: int = 50) -> list[dict]:
        with self._lock:
            c = self._conn.cursor()
            rows = c.execute("""
                SELECT id, tx_id, timestamp, merchant, category, amount_paise,
                       decision, reason, spendable_after_paise
                FROM vault_transactions
                ORDER BY id DESC LIMIT ?
            """, (limit,)).fetchall()

            return [
                {
                    "id"                   : r[0],
                    "tx_id"                : r[1],
                    "timestamp"            : r[2],
                    "merchant"             : r[3],
                    "category"             : r[4],
                    "amount_rupees"        : self.paise_to_rupees(r[5]),
                    "decision"             : r[6],
                    "reason"               : r[7],
                    "safe_to_spend_rupees" : self.paise_to_rupees(r[8])
                }
                for r in rows
            ]

    def close(self):
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                pass
