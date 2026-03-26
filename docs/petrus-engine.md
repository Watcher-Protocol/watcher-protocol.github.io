Petrus Detection Engine
Watcher Protocol — TINA + SCROLLFIRE PBC
Provisional patent filed March 9, 2026

What It Is
The Petrus Detection Engine is the scoring core of Watcher Protocol.
It evaluates evidence nodes across 17 dimensions (D1–D17) to determine
whether a claim is genuinely anchored or hallucinated.
Petrus — Latin for stone, foundation. A keystone is the piece that
holds the arch. Pull it and the structure collapses. The Petrus engine
finds those nodes.
Most evidence systems ask: is there a source?
Petrus asks: can this source bear weight?

The 17 Dimensions
Layer 1: Source Quality (D1–D3)
DimNameWhat It MeasuresD1Source AuthorityBase authority score by evidence type (judicial=1.0 → digital=0.55), with temporal decay at 2%/year for non-judicial sourcesD2Document AuthenticitySHA-256 hash presence and integrityD3Temporal ValidityRecency — last year=1.0, last 3 years=0.75, last decade=0.50, older=0.25
Layer 2: Coverage (D4–D6)
DimNameWhat It MeasuresD4Claim SpecificityDetail of the claim itself — vague claims score lowerD5Corroboration BreadthIndependent source domains — 4+ = full score. GATE: ≥ 0.60D6Source IndependenceFlood sub-gate — detects single-origin flooding. GATE: ≥ 0.55
Layer 3: Governance (D7–D11)
DimNameWhat It MeasuresD7Chain ContinuityTimestamp ordering and gap analysisD8Contradiction AbsenceAbsence of contradicting evidenceD9Scope AlignmentSemantic overlap between claim and evidenceD10Provenance IntegritySource author and URL presenceD11Recency WeightProportion of evidence from last 2 years
Layer 4: Expert and Legal (D12–D13)
DimNameWhat It MeasuresD12Expert ConsensusProportion of judicial, statutory, and expert-opinion sourcesD13Legal Standard ComplianceLegal-tier source density
Layer 5: Structural (D14–D16)
DimNameWhat It MeasuresD14Evidentiary TierAgreement across D1–D13 — high variance signals instabilityD15Cross-Reference DensityEvidence item count (log-scaled)D16Adversarial ResistanceNon-digital source ratio
D17: Keystone Centrality
Weighted composite of D1–D16. The Petrus Gate. Threshold: ≥ 0.75 → IMMUTABLE

Tier Assignments
ScoreTierMeaning≥ 0.75IMMUTABLEPetrus gate passed — cryptographically logged0.55–0.74PERSISTEDStrong evidence, decay applied over time0.35–0.54INGESTEDReceived, insufficient for persistence< 0.35REJECTEDGhost fact — no verifiable evidence anchor

Dimension Weights
D1  Source Authority          0.10
D2  Document Authenticity     0.08
D3  Temporal Validity         0.06
D4  Claim Specificity         0.07
D5  Corroboration Breadth     0.07
D6  Source Independence       0.08
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

Cross-Domain Validation
DomainClaimsResultAstrophysics (SN1987A)1313/13 PASSLegal hallucination—100%Financial fraud—100%Adversarial stress1313/13 PASSPublic health (epidemic)1818/18 PASSDisinformation2020/20 PASSAI alignment—45% AI error rate caught; 0 passed throughARC-AGI pattern recognition109/10; 1 honest uncertainty flaggedMulti-domain synthesis1515/15 PASSSeattle municipal blight1414/14; CRITICAL DRIFT DETECTED

Built by J. Wayne LaRosa-Perkins, Principal Architect — TINA + SCROLLFIRE PBC
Live demo: watcher-protocol.github.io
