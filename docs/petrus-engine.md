# Petrus Detection Engine

**Watcher Protocol — TINA + SCROLLFIRE PBC**  
Provisional patent filed March 9, 2026

---

## What It Is

The Petrus Detection Engine is the scoring core of Watcher Protocol.
It evaluates evidence nodes across 17 dimensions (D1–D17) to determine
whether a claim is genuinely anchored or hallucinated.

**Petrus** — Latin for stone, foundation. A keystone is the piece that
holds the arch. Pull it and the structure collapses. The Petrus engine
finds those nodes.

Most evidence systems ask: *is there a source?*  
Petrus asks: *can this source bear weight?*

---

## The 17 Dimensions

### Layer 1: Source Quality (D1–D3)

| Dim | Name | What It Measures |
|-----|------|-----------------|
| D1 | Source Authority | Base authority score by evidence type (judicial=1.0 → digital=0.55), with temporal decay at 2%/year for non-judicial sources |
| D2 | Document Authenticity | SHA-256 hash presence and integrity — verifies the evidence hasn't been modified |
| D3 | Temporal Validity | Recency of evidence — last year=1.0, last 3 years=0.75, last decade=0.50, older=0.25 |

### Layer 2: Coverage (D4–D6)

| Dim | Name | What It Measures |
|-----|------|-----------------|
| D4 | Claim Specificity | Specificity and detail of the claim itself — vague claims score lower |
| D5 | Corroboration Breadth | Number of independent source domains represented — 4+ domains = full score. **GATE: ≥ 0.60 required** |
| D6 | Source Independence | Flood sub-gate — detects evidence flooding from a single origin. Self-referential chains score near zero. **GATE: ≥ 0.55 required** |

> **EDGE-05 note:** D6 zero-anchor bug fixed. `anchor_count <= 0` now
> correctly triggers rejection (was `< 0`).

### Layer 3: Governance (D7–D11)

| Dim | Name | What It Measures |
|-----|------|-----------------|
| D7 | Chain Continuity | Timestamp ordering and gap analysis — gaps over 1 year penalized |
| D8 | Contradiction Absence | Absence of contradicting evidence — Phase 1 neutral; Phase 2 adds NLP detection |
| D9 | Scope Alignment | Semantic overlap between claim text and evidence content |
| D10 | Provenance Integrity | Presence of source author and URL — anonymous sources score lower |
| D11 | Recency Weight | Proportion of evidence from last 2 years |

### Layer 4: Expert and Legal (D12–D13)

| Dim | Name | What It Measures |
|-----|------|-----------------|
| D12 | Expert Consensus | Proportion of judicial, statutory, and expert-opinion sources |
| D13 | Legal Standard Compliance | Legal-tier source density — weighted toward judicial and public record |

### Layer 5: Structural (D14–D16)

| Dim | Name | What It Measures |
|-----|------|-----------------|
| D14 | Evidentiary Tier | Agreement across D1–D13 — high variance signals instability |
| D15 | Cross-Reference Density | Number of evidence items (log-scaled — 10 items = 1.0) |
| D16 | Adversarial Resistance | Non-digital source ratio — digital sources are easier to fabricate |

### D17: Keystone Centrality (Composite Gate)

The final weighted composite of D1–D16. This is the Petrus Gate.

**Threshold: ≥ 0.75 → IMMUTABLE**

---

## Tier Assignments

| Score | Tier | Meaning |
|-------|------|---------|
| ≥ 0.75 | IMMUTABLE | Petrus gate passed — cryptographically logged, permanently anchored |
| 0.55–0.74 | PERSISTED | Strong evidence, decay applied over time |
| 0.35–0.54 | INGESTED | Received but insufficient for persistence |
| < 0.35 | REJECTED | Ghost fact — no verifiable evidence anchor |

Gate failures (D5, D6, PII) trigger REJECTED regardless of composite score.

---

## Dimension Weights

```
D1  Source Authority          0.10
D2  Document Authenticity     0.08
D3  Temporal Validity         0.06
D4  Claim Specificity         0.07
D5  Corroboration Breadth     0.07
D6  Source Independence       0.08  ← elevated (flood sub-gate)
D7  Chain Continuity          0.06
D8  Contradiction Absence     0.07
D9  Scope Alignment           0.05
D10 Provenance Integrity      0.06
D11 Recency Weight            0.04
D12 Expert Consensus          0.04
D13 Legal Standard Compliance 0.06
D14 Evidentiary Tier          0.05
D15 Cross-Reference Density   0.04
D16 Adversarial Resistance    0.04
D17 Keystone Centrality       0.03
                              ────
                              1.00
```

---

## Real-World Validation

| Domain | Claims | Result |
|--------|--------|--------|
| Astrophysics (SN1987A) | 13 | 13/13 PASS |
| Legal hallucination | — | 100% |
| Financial fraud | — | 100% |
| Adversarial stress | 13 | 13/13 PASS |
| Public health (epidemic) | 18 | 18/18 PASS |
| Disinformation | 20 | 20/20 PASS |
| AI alignment | — | 45% AI error rate caught; 0 passed through |
| ARC-AGI pattern recognition | 10 | 9/10; 1 honest uncertainty flagged |
| Multi-domain synthesis | 15 | 15/15 PASS |
| Seattle municipal blight | 14 | 14/14; CRITICAL DRIFT DETECTED |

Same kernel. Same four gates. Ten domains. One architecture.

---

*Built by J. Wayne LaRosa-Perkins, Principal Architect — TINA + SCROLLFIRE PBC*  
*Live demo: watcher-protocol.github.io*
