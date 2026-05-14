"""
TINA + Scrollfire
Minimal Auditable Memory Demo

Demonstrates:
- evidence-weighted memory scoring
- governance vetoes
- delta override handling
- SHA-256 audit hashing
- tiered memory classification
- unit-testable behavior
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List
import hashlib
import json
import time
import unittest


class Tier(str, Enum):
    INTAKE = "INTAKE"
    ACTIVE = "ACTIVE"
    IMMUTABLE = "IMMUTABLE"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Evidence:
    kind: str
    strength: float
    ref: str = ""

    def __post_init__(self):
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Evidence strength must be between 0.0 and 1.0")


@dataclass(frozen=True)
class Governance:
    hard_veto: bool = False
    allow_delta_override: bool = False
    ethical_lock: bool = True
    decay_immune: bool = False


@dataclass
class MemoryMoment:
    claim: str
    timestamp: float = field(default_factory=time.time)
    evidence: List[Evidence] = field(default_factory=list)
    governance: Governance = field(default_factory=Governance)
    tags: List[str] = field(default_factory=list)
    source: str = "user"

    def stable_hash(self) -> str:
        payload = {
            "claim": self.claim,
            "timestamp": int(self.timestamp),
            "evidence": [asdict(e) for e in self.evidence],
            "governance": asdict(self.governance),
            "tags": sorted(self.tags),
            "source": self.source,
        }
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


@dataclass
class AuditResult:
    scroll_id: str
    tier: Tier
    evidentiary_value: float
    authority: float
    reason: str


@dataclass
class MemoryScroll:
    moment: MemoryMoment
    audit: AuditResult
    created_at: float
    last_review_at: float
    is_delta: bool = False


def compute_ev(moment: MemoryMoment) -> float:
    if "ghost" in moment.tags:
        return 0.0

    if not moment.evidence:
        return 0.1

    strengths = sorted((e.strength for e in moment.evidence), reverse=True)

    ev = 0.0
    weight = 1.0

    for strength in strengths:
        ev += strength * weight
        weight *= 0.5

    return min(1.0, ev)


def compute_authority(moment: MemoryMoment, ev: float) -> float:
    source_bonus = {
        "user": 0.05,
        "system": 0.10,
        "verified_record": 0.20,
    }.get(moment.source, 0.0)

    return min(1.0, ev + source_bonus)


def classify_tier(ev: float) -> Tier:
    if ev >= 0.85:
        return Tier.IMMUTABLE
    if ev >= 0.35:
        return Tier.ACTIVE
    return Tier.INTAKE


class ScrollfireLedger:
    def __init__(self):
        self.scrolls: Dict[str, MemoryScroll] = {}

    def ingest(self, moment: MemoryMoment, as_delta: bool = False) -> MemoryScroll:
        now = time.time()
        sid = moment.stable_hash()[:16]

        if moment.governance.hard_veto and not (
            as_delta and moment.governance.allow_delta_override
        ):
            audit = AuditResult(
                scroll_id=sid,
                tier=Tier.REJECTED,
                evidentiary_value=0.0,
                authority=0.0,
                reason="Rejected by hard governance veto",
            )
            return MemoryScroll(moment, audit, now, now, is_delta=as_delta)

        ev = compute_ev(moment)
        authority = compute_authority(moment, ev)
        tier = classify_tier(ev)

        audit = AuditResult(
            scroll_id=sid,
            tier=tier,
            evidentiary_value=ev,
            authority=authority,
            reason=f"Accepted into {tier.value} tier",
        )

        scroll = MemoryScroll(moment, audit, now, now, is_delta=as_delta)
        self.scrolls[sid] = scroll
        return scroll


class TestHarness(unittest.TestCase):
    def setUp(self):
        self.ledger = ScrollfireLedger()

    def test_veto_rejects_claim(self):
        moment = MemoryMoment(
            "Blocked claim",
            governance=Governance(hard_veto=True),
        )
        scroll = self.ledger.ingest(moment)
        self.assertEqual(scroll.audit.tier, Tier.REJECTED)

    def test_delta_override_bypasses_veto(self):
        moment = MemoryMoment(
            "Override claim",
            governance=Governance(
                hard_veto=True,
                allow_delta_override=True,
            ),
        )
        scroll = self.ledger.ingest(moment, as_delta=True)
        self.assertNotEqual(scroll.audit.tier, Tier.REJECTED)

    def test_ghost_claim_has_zero_ev(self):
        moment = MemoryMoment("Ghost claim", tags=["ghost"])
        scroll = self.ledger.ingest(moment)
        self.assertEqual(scroll.audit.evidentiary_value, 0.0)

    def test_strong_evidence_becomes_immutable(self):
        moment = MemoryMoment(
            "Strongly supported claim",
            evidence=[
                Evidence("document", 0.9, "court_record.pdf"),
                Evidence("hash", 0.8, "sha256:abc123"),
            ],
            source="verified_record",
        )
        scroll = self.ledger.ingest(moment)
        self.assertEqual(scroll.audit.tier, Tier.IMMUTABLE)


if __name__ == "__main__":
    unittest.main()
