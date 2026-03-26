"""
Watcher Protocol — Four-Gate Governance Kernel
TINA + SCROLLFIRE PBC
Provisional patent filed March 9, 2026

Gate 1: Ingestion — PII check, claim receipt
Gate 2: Evidence Scoring — Petrus D1-D17
Gate 3: Tier Assignment — IMMUTABLE / PERSISTED / INGESTED / REJECTED
Gate 4: Immutable Logging — SHA-256 audit ledger

Nothing passes without evidence. Nothing is deleted once logged.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import re

from .petrus import Claim, Evidence, ClaimTier, run_petrus, PetrusResult
from .ledger import AuditLedger, LedgerEntry


# ---------------------------------------------------------------------------
# PII detection (Gate 1)
# ---------------------------------------------------------------------------

PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",           # SSN
    r"\b\d{16}\b",                        # Credit card (simplified)
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone
]

def check_pii(text: str) -> tuple[bool, list[str]]:
    """Returns (pii_found, list_of_findings)."""
    findings = []
    for pattern in PII_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            findings.append(f"PII pattern matched: {pattern}")
    return bool(findings), findings


# ---------------------------------------------------------------------------
# Governance result
# ---------------------------------------------------------------------------

@dataclass
class GovernanceResult:
    claim_id: str
    tier: ClaimTier
    verdict: str
    composite_score: float
    gate_failures: list[str]
    pii_findings: list[str]
    petrus_result: PetrusResult
    ledger_entry: Optional[LedgerEntry]
    timestamp: str

    def passed(self) -> bool:
        return self.tier in (ClaimTier.IMMUTABLE, ClaimTier.PERSISTED)

    def summary(self) -> str:
        lines = [
            f"CLAIM:     {self.claim_id}",
            f"TIER:      {self.tier.value}",
            f"SCORE:     {self.composite_score:.4f}",
            f"VERDICT:   {self.verdict}",
            f"PII:       {'FLAGGED' if self.pii_findings else 'CLEAR'}",
            f"TIMESTAMP: {self.timestamp}",
        ]
        if self.gate_failures:
            lines.append(f"FAILURES:  {'; '.join(self.gate_failures)}")
        if self.ledger_entry:
            lines.append(f"LEDGER:    {self.ledger_entry.entry_id} [{self.ledger_entry.integrity_status}]")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Governance kernel
# ---------------------------------------------------------------------------

class GovernanceKernel:
    """
    The four-gate governance kernel. Entry point for all claim processing.

    Usage:
        kernel = GovernanceKernel()
        claim = Claim(id="C001", text="...", evidence_pool=[...])
        result = kernel.process(claim)
        print(result.summary())
    """

    def __init__(self, ledger_path: str = "watcher_ledger.db"):
        self.ledger = AuditLedger(db_path=ledger_path)
        self.processed = 0
        self.rejected = 0

    def process(self, claim: Claim) -> GovernanceResult:
        """
        Run a claim through all four governance gates.

        Gate 1 — Ingestion: PII check
        Gate 2 — Evidence Scoring: Petrus D1-D17
        Gate 3 — Tier Assignment: IMMUTABLE/PERSISTED/INGESTED/REJECTED
        Gate 4 — Immutable Logging: SHA-256 ledger write
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        gate_failures = []

        # ── Gate 1: Ingestion / PII ─────────────────────────────────────
        pii_found, pii_findings = check_pii(claim.text)
        if pii_found:
            gate_failures.append(f"GATE 1: PII DETECTED — {'; '.join(pii_findings)}")

        # ── Gate 2: Evidence Scoring ────────────────────────────────────
        petrus_result = run_petrus(claim)
        gate_failures.extend(petrus_result.gate_failures)

        # ── Gate 3: Tier Assignment ─────────────────────────────────────
        tier = petrus_result.tier
        verdict = petrus_result.verdict

        if pii_found and tier != ClaimTier.REJECTED:
            tier = ClaimTier.REJECTED
            verdict = f"REJECTED — PII detected: {'; '.join(pii_findings)}"

        # ── Gate 4: Immutable Logging ───────────────────────────────────
        ledger_entry = self.ledger.write(
            claim_id=claim.id,
            tier=tier.value,
            verdict=verdict,
            composite_score=petrus_result.composite_score,
            gate_failures=gate_failures,
        )

        self.processed += 1
        if tier == ClaimTier.REJECTED:
            self.rejected += 1

        return GovernanceResult(
            claim_id=claim.id,
            tier=tier,
            verdict=verdict,
            composite_score=petrus_result.composite_score,
            gate_failures=gate_failures,
            pii_findings=pii_findings,
            petrus_result=petrus_result,
            ledger_entry=ledger_entry,
            timestamp=timestamp,
        )

    def process_batch(self, claims: list[Claim]) -> list[GovernanceResult]:
        """Process multiple claims. Returns all results."""
        return [self.process(claim) for claim in claims]

    def stats(self) -> dict:
        return {
            "processed": self.processed,
            "rejected": self.rejected,
            "passed": self.processed - self.rejected,
            "rejection_rate": self.rejected / max(self.processed, 1),
            "ledger": self.ledger.summary(),
        }
