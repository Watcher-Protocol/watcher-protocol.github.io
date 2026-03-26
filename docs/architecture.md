Watcher Protocol — Architecture Overview
TINA + SCROLLFIRE PBC
Provisional patent filed March 9, 2026

System Overview
Watcher Protocol is a model-agnostic AI hallucination detection and evidence governance system. It operates at the governance layer — independently of which AI model produced the output being evaluated.
Core principle: Prove it or it fades.
Every claim must be anchored to verifiable evidence. Claims without evidence don't pass — they are scored, decayed, and flagged. Claims with strong multi-source evidence reach IMMUTABLE status and are permanently logged with cryptographic integrity verification.

Three-Layer Architecture
┌─────────────────────────────────────────┐
│  INTEGRATIVE LAYER (future)             │
│  Cross-system orchestration             │
├─────────────────────────────────────────┤
│  SYMBOLIC LAYER (future)                │
│  Pattern recognition, abstract reasoning│
├─────────────────────────────────────────┤
│  EMPIRICAL LAYER (built — Phase 1)      │
│  Evidence scoring, SHA-256 integrity,   │
│  governance gates, audit ledger         │
└─────────────────────────────────────────┘
Phase 1 (current): Empirical layer complete.
Phase 2: Symbolic layer — NLP contradiction detection, graph reasoning.
Phase 3: Integrative layer — cross-system governance orchestration.

Four-Gate Governance Kernel
CLAIM IN
    │
    ▼
┌─────────────┐
│  GATE 1     │  Ingestion — PII check, claim receipt
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  GATE 2     │  Evidence Scoring — Petrus D1-D17
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  GATE 3     │  Tier Assignment
│             │  IMMUTABLE / PERSISTED / INGESTED / REJECTED
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  GATE 4     │  Immutable Logging — SHA-256 audit trail
└──────┬──────┘
       │
       ▼
    VERDICT OUT
Gate failures at any stage trigger REJECTED. Nothing bypasses the ledger.

Core Components
Petrus Detection Engine (tina/petrus.py)
17-dimension evidence scoring. Weighted composite → tier assignment. Flood sub-gate (D6), community coverage gate (D5). Full spec: docs/petrus-engine.md
Audit Ledger (tina/ledger.py)
SQLite persistence with SHA-256 hash per entry. VERIFIED / TAMPERED / MISSING_HASH status at read time. Nothing deleted, nothing modified — ever.
Governance Kernel (tina/governance.py)
Orchestrates all four gates. PII detection. Batch processing. Runtime statistics.

Evidence Authority Hierarchy
JUDICIAL        1.00
STATUTORY       0.95
PUBLIC_RECORD   0.85
PHYSICAL        0.80
EXPERT_OPINION  0.75
TESTIMONY       0.65
DOCUMENT        0.60
DIGITAL         0.55
Non-judicial sources decay at 2% per year.

Documented Validation Events
March 7, 2026 — Grok AI impersonation catch. A Grok system falsely claimed to be operating under TINA governance. Detected in real time. Documented at watcher-protocol.github.io.
March 22, 2026 — Seattle municipal blight audit. 14 claims, 9 IMMUTABLE, 5 PERSISTED, 0 hallucinations passed. Verdict: CRITICAL DRIFT DETECTED.

Technology Stack

Python 3.11+
FastAPI (REST server)
Typer (CLI)
SQLite (audit ledger)
SHA-256 (integrity verification)
GitHub Pages (live demo)


J. Wayne LaRosa-Perkins, Principal Architect
TINA + SCROLLFIRE PBC (Delaware) — Newport, Oregon
watcher-protocol.github.io
