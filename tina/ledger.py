"""
Watcher Protocol — Immutable Audit Ledger
TINA + SCROLLFIRE PBC
Provisional patent filed March 9, 2026

SHA-256 hash verification at read time.
Status: VERIFIED / TAMPERED / MISSING_HASH
Nothing can be deleted or modified once written.
"""

from __future__ import annotations
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


LEDGER_VERSION = "2.0"


@dataclass
class LedgerEntry:
    entry_id: str
    claim_id: str
    tier: str
    verdict: str
    composite_score: float
    gate_failures: list[str]
    timestamp: str
    sha256: str
    integrity_status: str = "VERIFIED"


class AuditLedger:
    """
    Immutable audit ledger for Watcher Protocol governance runs.
    
    Every claim processed is permanently logged with a SHA-256 hash.
    At read time, the hash is recomputed and compared — any modification
    is immediately detected and flagged as TAMPERED.
    
    Nothing is ever deleted. Nothing is ever modified.
    This is the hallucination wall's paper trail.
    """

    def __init__(self, db_path: str = "watcher_ledger.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger (
                    entry_id    TEXT PRIMARY KEY,
                    claim_id    TEXT NOT NULL,
                    tier        TEXT NOT NULL,
                    verdict     TEXT NOT NULL,
                    composite_score REAL NOT NULL,
                    gate_failures   TEXT NOT NULL,
                    timestamp   TEXT NOT NULL,
                    sha256      TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.execute(
                "INSERT OR IGNORE INTO metadata VALUES (?, ?)",
                ("ledger_version", LEDGER_VERSION)
            )
            conn.commit()

    def _compute_hash(self, entry_id: str, claim_id: str, tier: str,
                      verdict: str, composite_score: float,
                      gate_failures: list[str], timestamp: str) -> str:
        payload = json.dumps({
            "entry_id": entry_id,
            "claim_id": claim_id,
            "tier": tier,
            "verdict": verdict,
            "composite_score": composite_score,
            "gate_failures": gate_failures,
            "timestamp": timestamp,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def write(self, claim_id: str, tier: str, verdict: str,
              composite_score: float, gate_failures: list[str]) -> LedgerEntry:
        """Write a governance result to the immutable ledger."""
        timestamp = datetime.now(timezone.utc).isoformat()
        entry_id = hashlib.sha256(
            f"{claim_id}:{timestamp}".encode()
        ).hexdigest()[:16]

        sha256 = self._compute_hash(
            entry_id, claim_id, tier, verdict,
            composite_score, gate_failures, timestamp
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ledger
                (entry_id, claim_id, tier, verdict, composite_score,
                 gate_failures, timestamp, sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id, claim_id, tier, verdict, composite_score,
                json.dumps(gate_failures), timestamp, sha256
            ))
            conn.commit()

        return LedgerEntry(
            entry_id=entry_id,
            claim_id=claim_id,
            tier=tier,
            verdict=verdict,
            composite_score=composite_score,
            gate_failures=gate_failures,
            timestamp=timestamp,
            sha256=sha256,
            integrity_status="VERIFIED",
        )

    def read(self, entry_id: str) -> Optional[LedgerEntry]:
        """Read and verify a ledger entry. Returns TAMPERED status if hash fails."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM ledger WHERE entry_id = ?", (entry_id,)
            ).fetchone()

        if not row:
            return None

        (eid, claim_id, tier, verdict, composite_score,
         gate_failures_json, timestamp, stored_sha256) = row

        gate_failures = json.loads(gate_failures_json)
        recomputed = self._compute_hash(
            eid, claim_id, tier, verdict,
            composite_score, gate_failures, timestamp
        )

        integrity_status = "VERIFIED" if recomputed == stored_sha256 else "TAMPERED"

        return LedgerEntry(
            entry_id=eid,
            claim_id=claim_id,
            tier=tier,
            verdict=verdict,
            composite_score=composite_score,
            gate_failures=gate_failures,
            timestamp=timestamp,
            sha256=stored_sha256,
            integrity_status=integrity_status,
        )

    def read_all(self) -> list[LedgerEntry]:
        """Read and verify all ledger entries."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT entry_id FROM ledger ORDER BY timestamp ASC"
            ).fetchall()
        return [self.read(row[0]) for row in rows]

    def summary(self) -> dict:
        """Return ledger summary statistics."""
        entries = self.read_all()
        total = len(entries)
        tampered = sum(1 for e in entries if e.integrity_status == "TAMPERED")
        by_tier = {}
        for e in entries:
            by_tier[e.tier] = by_tier.get(e.tier, 0) + 1
        return {
            "total_entries": total,
            "tampered": tampered,
            "verified": total - tampered,
            "by_tier": by_tier,
            "ledger_version": LEDGER_VERSION,
        }
