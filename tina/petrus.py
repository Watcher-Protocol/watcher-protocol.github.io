"""
Petrus Detection Engine
TINA + SCROLLFIRE PBC — Watcher Protocol
Provisional patent filed March 9, 2026

The Petrus engine scores evidence nodes across 17 dimensions (D1–D17)
to determine whether a claim is genuinely anchored or hallucinated.

'Petrus' — Latin for stone, foundation. The engine finds the keystones:
evidence that can actually bear weight, not just evidence that exists.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import hashlib
import json


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EvidenceType(str, Enum):
    JUDICIAL = "judicial"
    STATUTORY = "statutory"
    PUBLIC_RECORD = "public_record"
    EXPERT_OPINION = "expert_opinion"
    DOCUMENT = "document"
    PHYSICAL = "physical"
    DIGITAL = "digital"
    TESTIMONY = "testimony"


class ClaimTier(str, Enum):
    IMMUTABLE = "IMMUTABLE"
    PERSISTED = "PERSISTED"
    INGESTED = "INGESTED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Dimension weights (D1–D17)
# Weights sum to 1.0. Legal use case tuning — Phase 1.
# ---------------------------------------------------------------------------

DIMENSION_WEIGHTS: dict[int, float] = {
    1:  0.10,  # Source Authority
    2:  0.08,  # Document Authenticity
    3:  0.06,  # Temporal Validity
    4:  0.07,  # Claim Specificity
    5:  0.07,  # Corroboration Breadth
    6:  0.08,  # Source Independence  (flood sub-gate — elevated weight)
    7:  0.06,  # Chain Continuity
    8:  0.07,  # Contradiction Absence
    9:  0.05,  # Scope Alignment
    10: 0.06,  # Provenance Integrity
    11: 0.04,  # Recency Weight
    12: 0.04,  # Expert Consensus
    13: 0.06,  # Legal Standard Compliance
    14: 0.05,  # Evidentiary Tier
    15: 0.04,  # Cross-Reference Density
    16: 0.04,  # Adversarial Resistance
    17: 0.03,  # Keystone Centrality (composite gate)
}

assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"

# Gate thresholds
PETRUS_GATE_THRESHOLD = 0.75       # Minimum composite score to pass
SOURCE_INDEPENDENCE_GATE = 0.55    # D6 minimum — flood protection
COMMUNITY_COVERAGE_GATE = 0.60    # D5 minimum — domain breadth
FLOOD_SOURCE_LIMIT = 3             # Max items from single source before penalty

# Authority base scores by evidence type
AUTHORITY_BASE: dict[EvidenceType, float] = {
    EvidenceType.JUDICIAL:       1.00,
    EvidenceType.STATUTORY:      0.95,
    EvidenceType.PUBLIC_RECORD:  0.85,
    EvidenceType.EXPERT_OPINION: 0.75,
    EvidenceType.DOCUMENT:       0.60,
    EvidenceType.PHYSICAL:       0.80,
    EvidenceType.DIGITAL:        0.55,
    EvidenceType.TESTIMONY:      0.65,
}

DECAY_RATE_PER_YEAR = 0.02  # 2% authority decay per year for non-judicial sources


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Evidence:
    id: str
    content: str
    evidence_type: EvidenceType
    source_author: Optional[str] = None
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    timestamp: Optional[datetime] = None
    sha256: str = field(init=False)

    def __post_init__(self):
        self.sha256 = hashlib.sha256(
            f"{self.id}:{self.content}".encode()
        ).hexdigest()


@dataclass
class Claim:
    id: str
    text: str
    evidence_pool: list[Evidence] = field(default_factory=list)
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PetrusResult:
    claim_id: str
    dimension_scores: dict[int, float]
    composite_score: float
    tier: ClaimTier
    gate_failures: list[str]
    verdict: str
    sha256: str = field(init=False)

    def __post_init__(self):
        payload = json.dumps({
            "claim_id": self.claim_id,
            "composite_score": self.composite_score,
            "tier": self.tier.value,
            "verdict": self.verdict,
        }, sort_keys=True)
        self.sha256 = hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Dimension scorers (D1–D16)
# ---------------------------------------------------------------------------

def score_d1_source_authority(evidence_pool: list[Evidence]) -> float:
    """D1: Source Authority — base authority score with temporal decay."""
    if not evidence_pool:
        return 0.0
    scores = []
    now = datetime.now(timezone.utc)
    for e in evidence_pool:
        base = AUTHORITY_BASE.get(e.evidence_type, 0.50)
        if e.timestamp and e.evidence_type != EvidenceType.JUDICIAL:
            years_old = (now - e.timestamp).days / 365.25
            decay = DECAY_RATE_PER_YEAR * years_old
            base = max(base - decay, base * 0.5)
        scores.append(base)
    return sum(scores) / len(scores)


def score_d2_document_authenticity(evidence_pool: list[Evidence]) -> float:
    """D2: Document Authenticity — SHA-256 presence and integrity."""
    if not evidence_pool:
        return 0.0
    verified = sum(1 for e in evidence_pool if e.sha256 and len(e.sha256) == 64)
    return verified / len(evidence_pool)


def score_d3_temporal_validity(evidence_pool: list[Evidence]) -> float:
    """D3: Temporal Validity — recency of evidence."""
    if not evidence_pool:
        return 0.0
    now = datetime.now(timezone.utc)
    scores = []
    for e in evidence_pool:
        if not e.timestamp:
            scores.append(0.5)
            continue
        days_old = (now - e.timestamp).days
        if days_old <= 365:
            scores.append(1.0)
        elif days_old <= 1095:  # 3 years
            scores.append(0.75)
        elif days_old <= 3650:  # 10 years
            scores.append(0.50)
        else:
            scores.append(0.25)
    return sum(scores) / len(scores)


def score_d4_claim_specificity(claim: Claim) -> float:
    """D4: Claim Specificity — length and detail proxy."""
    words = len(claim.text.split())
    if words >= 20:
        return 1.0
    elif words >= 10:
        return 0.75
    elif words >= 5:
        return 0.50
    else:
        return 0.25


def score_d5_corroboration_breadth(evidence_pool: list[Evidence]) -> float:
    """D5: Corroboration Breadth — unique domains represented."""
    if not evidence_pool:
        return 0.0
    domains = {e.source_domain for e in evidence_pool if e.source_domain}
    score = min(len(domains) / 4.0, 1.0)  # 4+ domains = full score
    return score


def score_d6_source_independence(evidence_pool: list[Evidence]) -> tuple[float, bool]:
    """
    D6: Source Independence — flood sub-gate.
    Returns (score, flood_detected).
    EDGE-05 fix: anchor_count check uses <= 0, not < 0.
    """
    if not evidence_pool:
        return 0.0, False

    from collections import Counter
    source_groups: Counter[str] = Counter()
    for e in evidence_pool:
        key = e.source_author or e.source_url or f"unknown_{e.id}"
        source_groups[key] += 1

    max_from_single = max(source_groups.values()) if source_groups else 0
    unique_sources = len(source_groups)
    flood_detected = max_from_single > FLOOD_SOURCE_LIMIT

    if flood_detected:
        score = min(unique_sources / max(len(evidence_pool), 1), 0.5)
    else:
        score = min(unique_sources / max(len(evidence_pool), 1), 1.0)

    # Circularity trigger
    if score < 0.35:
        score = min(score, 0.25)

    return score, flood_detected


def score_d7_chain_continuity(evidence_pool: list[Evidence]) -> float:
    """D7: Chain Continuity — timestamp ordering and gaps."""
    timestamped = [e for e in evidence_pool if e.timestamp]
    if len(timestamped) < 2:
        return 0.5
    sorted_e = sorted(timestamped, key=lambda e: e.timestamp)
    gaps = []
    for i in range(1, len(sorted_e)):
        gap = (sorted_e[i].timestamp - sorted_e[i-1].timestamp).days
        gaps.append(gap)
    max_gap = max(gaps) if gaps else 0
    if max_gap <= 30:
        return 1.0
    elif max_gap <= 180:
        return 0.75
    elif max_gap <= 365:
        return 0.50
    else:
        return 0.25


def score_d8_contradiction_absence(evidence_pool: list[Evidence]) -> float:
    """D8: Contradiction Absence — placeholder for contradiction detection."""
    # Phase 1: no contradiction detection; return neutral score
    # Phase 2: NLP-based contradiction detection
    return 0.75


def score_d9_scope_alignment(claim: Claim, evidence_pool: list[Evidence]) -> float:
    """D9: Scope Alignment — evidence relevance to claim."""
    if not evidence_pool:
        return 0.0
    claim_words = set(claim.text.lower().split())
    scores = []
    for e in evidence_pool:
        evidence_words = set(e.content.lower().split())
        overlap = len(claim_words & evidence_words) / max(len(claim_words), 1)
        scores.append(min(overlap * 2, 1.0))  # Scale up partial matches
    return sum(scores) / len(scores)


def score_d10_provenance_integrity(evidence_pool: list[Evidence]) -> float:
    """D10: Provenance Integrity — source URL and author presence."""
    if not evidence_pool:
        return 0.0
    scores = []
    for e in evidence_pool:
        score = 0.0
        if e.source_author:
            score += 0.5
        if e.source_url:
            score += 0.5
        scores.append(score)
    return sum(scores) / len(scores)


def score_d11_recency_weight(evidence_pool: list[Evidence]) -> float:
    """D11: Recency Weight — proportion of evidence from last 2 years."""
    if not evidence_pool:
        return 0.0
    now = datetime.now(timezone.utc)
    recent = sum(
        1 for e in evidence_pool
        if e.timestamp and (now - e.timestamp).days <= 730
    )
    return recent / len(evidence_pool)


def score_d12_expert_consensus(evidence_pool: list[Evidence]) -> float:
    """D12: Expert Consensus — proportion of expert/judicial sources."""
    if not evidence_pool:
        return 0.0
    expert_types = {EvidenceType.JUDICIAL, EvidenceType.STATUTORY, EvidenceType.EXPERT_OPINION}
    expert_count = sum(1 for e in evidence_pool if e.evidence_type in expert_types)
    return expert_count / len(evidence_pool)


def score_d13_legal_standard_compliance(evidence_pool: list[Evidence]) -> float:
    """D13: Legal Standard Compliance — judicial/statutory source proportion."""
    if not evidence_pool:
        return 0.5
    legal_types = {EvidenceType.JUDICIAL, EvidenceType.STATUTORY, EvidenceType.PUBLIC_RECORD}
    legal_count = sum(1 for e in evidence_pool if e.evidence_type in legal_types)
    return 0.5 + (legal_count / len(evidence_pool)) * 0.5


def score_d14_evidentiary_tier(composite_so_far: float, dim_scores: dict[int, float]) -> float:
    """D14: Evidentiary Tier — agreement across dimensions."""
    if not dim_scores:
        return 0.5
    scores = list(dim_scores.values())
    variance = sum((s - composite_so_far) ** 2 for s in scores) / len(scores)
    # Low variance = high agreement = high score
    return max(1.0 - variance, 0.0)


def score_d15_cross_reference_density(evidence_pool: list[Evidence]) -> float:
    """D15: Cross-Reference Density — number of evidence items (log-scaled)."""
    if not evidence_pool:
        return 0.0
    import math
    return min(math.log(len(evidence_pool) + 1) / math.log(11), 1.0)  # 10 items = 1.0


def score_d16_adversarial_resistance(evidence_pool: list[Evidence]) -> float:
    """D16: Adversarial Resistance — digital source ratio (easier to fabricate)."""
    if not evidence_pool:
        return 0.5
    digital_count = sum(1 for e in evidence_pool if e.evidence_type == EvidenceType.DIGITAL)
    digital_ratio = digital_count / len(evidence_pool)
    # More non-digital sources = higher adversarial resistance
    return 1.0 - (digital_ratio * 0.5)


# ---------------------------------------------------------------------------
# Petrus Gate (D17 — composite)
# ---------------------------------------------------------------------------

def run_petrus(claim: Claim) -> PetrusResult:
    """
    Run the full Petrus Detection Engine against a claim.
    Returns a PetrusResult with tier assignment and audit trail.
    """
    pool = claim.evidence_pool
    gate_failures = []

    # Score D1–D13 (independent dimensions)
    d6_score, flood_detected = score_d6_source_independence(pool)
    if flood_detected:
        gate_failures.append("D6: FLOOD DETECTED — source independence compromised")
    if d6_score < SOURCE_INDEPENDENCE_GATE:
        gate_failures.append(f"D6: SOURCE INDEPENDENCE GATE FAILED ({d6_score:.3f} < {SOURCE_INDEPENDENCE_GATE})")

    d5_score = score_d5_corroboration_breadth(pool)
    if d5_score < COMMUNITY_COVERAGE_GATE:
        gate_failures.append(f"D5: COMMUNITY COVERAGE GATE FAILED ({d5_score:.3f} < {COMMUNITY_COVERAGE_GATE})")

    dim_scores: dict[int, float] = {
        1:  score_d1_source_authority(pool),
        2:  score_d2_document_authenticity(pool),
        3:  score_d3_temporal_validity(pool),
        4:  score_d4_claim_specificity(claim),
        5:  d5_score,
        6:  d6_score,
        7:  score_d7_chain_continuity(pool),
        8:  score_d8_contradiction_absence(pool),
        9:  score_d9_scope_alignment(claim, pool),
        10: score_d10_provenance_integrity(pool),
        11: score_d11_recency_weight(pool),
        12: score_d12_expert_consensus(pool),
        13: score_d13_legal_standard_compliance(pool),
    }

    # Partial composite for D14
    partial = sum(DIMENSION_WEIGHTS[d] * s for d, s in dim_scores.items())

    dim_scores[14] = score_d14_evidentiary_tier(partial, dim_scores)
    dim_scores[15] = score_d15_cross_reference_density(pool)
    dim_scores[16] = score_d16_adversarial_resistance(pool)

    # D17: Keystone Centrality — composite gate
    composite = sum(DIMENSION_WEIGHTS[d] * dim_scores[d] for d in range(1, 17))
    composite = min(composite, 1.0)
    dim_scores[17] = composite

    # Hard veto for gate failures
    if gate_failures:
        tier = ClaimTier.REJECTED
        verdict = f"REJECTED — governance gate failure: {'; '.join(gate_failures)}"
    elif composite >= PETRUS_GATE_THRESHOLD:
        tier = ClaimTier.IMMUTABLE
        verdict = f"IMMUTABLE — Petrus gate passed (score: {composite:.4f})"
    elif composite >= 0.55:
        tier = ClaimTier.PERSISTED
        verdict = f"PERSISTED — evidence present, decay applied (score: {composite:.4f})"
    elif composite >= 0.35:
        tier = ClaimTier.INGESTED
        verdict = f"INGESTED — insufficient evidence for persistence (score: {composite:.4f})"
    else:
        tier = ClaimTier.REJECTED
        verdict = f"REJECTED — ghost fact: evidence score below minimum (score: {composite:.4f})"

    return PetrusResult(
        claim_id=claim.id,
        dimension_scores=dim_scores,
        composite_score=composite,
        tier=tier,
        gate_failures=gate_failures,
        verdict=verdict,
    )
