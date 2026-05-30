#!/usr/bin/env python3
"""
tina_confidence_layer.py
TINA Confidence Transparency Layer
TINA + SCROLLFIRE PBC — J. Wayne LaRosa-Perkins

Philosophy:
  Nothing is blocked. Everything is scored.
  The system tells the truth about confidence and tries to improve it.
  The operator decides what to do with that information.

Replaces: HallucinationGate92 (blocking model)
Becomes:  Confidence refinement loop + honest output labeling
"""

import time
from dataclasses import dataclass, field
from typing import Optional

# ── D1-D17 Dimension Labels (Petrus Engine) ────────────────────────
PETRUS_DIMENSIONS = {
    "D1":  "Source authenticity",
    "D2":  "Attribution clarity",
    "D3":  "Temporal consistency",
    "D4":  "Internal coherence",
    "D5":  "Corroboration breadth",
    "D6":  "Single-origin flood check",
    "D7":  "Inflation language detection",
    "D8":  "Claim-to-evidence ratio",
    "D9":  "Counterfactual resistance",
    "D10": "Source independence",
    "D11": "Logical chain integrity",
    "D12": "Context preservation",
    "D13": "Specificity grounding",
    "D14": "Dimension disagreement",
    "D15": "Provenance depth",
    "D16": "Temporal decay",
    "D17": "Petrus Gate (composite)",
}

CONFIDENCE_BANDS = {
    (0.85, 1.00): ("OPERATIONAL", "#3fb950"),
    (0.70, 0.85): ("STRONG",       "#58a6ff"),
    (0.51, 0.70): ("SUPPORTED",    "#bc8cff"),
    (0.31, 0.51): ("SPECULATIVE",  "#d6b46a"),
    (0.00, 0.31): ("WEAK",         "#f85149"),
}

def confidence_band(score: float) -> tuple[str, str]:
    for (low, high), (label, color) in CONFIDENCE_BANDS.items():
        if low <= score <= high:
            return label, color
    return "WEAK", "#f85149"


@dataclass
class ConfidenceReport:
    """
    What comes out of the transparency layer.
    The response is always included. Nothing is blocked.
    """
    response: str
    initial_score: float
    final_score: float
    iterations: int
    band: str
    band_color: str
    weak_dimensions: list[str]
    refinement_notes: list[str]
    audit_trail: list[str] = field(default_factory=list)
    confidence_tier: str = "CLAIMED"

    def render_label(self) -> str:
        delta = self.final_score - self.initial_score
        delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
        return (
            f"[{self.band}] Confidence: {self.final_score:.2f} "
            f"(started {self.initial_score:.2f}, {delta_str} after {self.iterations} pass{'es' if self.iterations != 1 else ''})"
        )

    def render_weak_dims(self) -> str:
        if not self.weak_dimensions:
            return "All dimensions nominal."
        return "Weak dimensions: " + ", ".join(self.weak_dimensions)


class TINAConfidenceLayer:
    """
    Scores Oracle output against Petrus D1-D17.
    Runs a refinement loop to push score toward 100%.
    Always returns the response. Never blocks.
    """

    MAX_ITERATIONS = 3
    TARGET = 0.92

    def __init__(self, evidence_ledger: Optional[list] = None):
        """
        evidence_ledger: list of source dicts from the active case.
        If None, scoring runs without ledger corroboration.
        """
        self.ledger = evidence_ledger or []
        self._log: list[str] = []

    def _stamp(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self._log.append(entry)

    def _score_dimensions(self, response: str, query: str) -> dict[str, float]:
        """
        Score each Petrus dimension against the response text.
        In production: wire each dimension to the real Petrus scoring logic.
        These are honest placeholder heuristics until full integration.
        """
        text = response.lower()
        scores = {}

        # D1 — Source authenticity: does it cite anything?
        scores["D1"] = 0.85 if any(w in text for w in ["v.", "u.s.c", "§", "filed", "record", "exhibit"]) else 0.55

        # D2 — Attribution clarity: named sources?
        scores["D2"] = 0.88 if any(w in text for w in ["according to", "per", "as stated", "defendant", "plaintiff"]) else 0.60

        # D3 — Temporal consistency: dates present?
        import re
        scores["D3"] = 0.90 if re.search(r'\b(19|20)\d{2}\b', response) else 0.62

        # D4 — Internal coherence: no self-contradiction markers
        contradiction_markers = ["however, it also says", "contradicts itself", "on the other hand it states"]
        scores["D4"] = 0.55 if any(m in text for m in contradiction_markers) else 0.87

        # D5 — Corroboration breadth: multiple sources in ledger referenced?
        ledger_hits = sum(1 for s in self.ledger if s.get("label", "").lower() in text)
        scores["D5"] = min(0.95, 0.60 + (ledger_hits * 0.10))

        # D6 — Single-origin flood: is one source dominating?
        scores["D6"] = 0.55 if text.count("according to") > 3 else 0.88

        # D7 — Inflation language
        inflation = ["obviously", "clearly proves", "undeniably", "without question", "certainly"]
        scores["D7"] = 0.50 if any(w in text for w in inflation) else 0.90

        # D8 — Claim-to-evidence ratio: claims without backing
        claim_words = len(re.findall(r'\b(claim|assert|allege|contend|argue)\b', text))
        evidence_words = len(re.findall(r'\b(evidence|document|record|exhibit|filing)\b', text))
        ratio = evidence_words / max(claim_words, 1)
        scores["D8"] = min(0.95, 0.55 + (ratio * 0.15))

        # D9 — Counterfactual resistance: does it acknowledge alternatives?
        scores["D9"] = 0.82 if any(w in text for w in ["however", "alternatively", "counter", "dispute", "could also"]) else 0.68

        # D10 — Source independence: ledger diversity
        unique_types = len(set(s.get("source_type", "unknown") for s in self.ledger))
        scores["D10"] = min(0.95, 0.60 + (unique_types * 0.08))

        # D11 — Logical chain integrity
        scores["D11"] = 0.85

        # D12 — Context preservation: response addresses the query
        query_words = set(query.lower().split())
        response_words = set(text.split())
        overlap = len(query_words & response_words) / max(len(query_words), 1)
        scores["D12"] = min(0.95, 0.55 + overlap)

        # D13 — Specificity grounding: specific vs vague
        vague = ["something", "somehow", "probably", "maybe", "might be", "could be"]
        vague_count = sum(text.count(w) for w in vague)
        scores["D13"] = max(0.45, 0.90 - (vague_count * 0.05))

        # D14 — Dimension disagreement: internal register conflicts
        legal_register = any(w in text for w in ["pursuant", "whereas", "aforementioned", "herein"])
        mythic_register = any(w in text for w in ["prophecy", "flame", "cosmic", "decree", "codex"])
        scores["D14"] = 0.60 if (legal_register and mythic_register) else 0.88

        # D15 — Provenance depth
        scores["D15"] = min(0.95, 0.65 + (len(self.ledger) * 0.05))

        # D16 — Temporal decay (placeholder — would use source age)
        scores["D16"] = 0.85

        # D17 — Petrus Gate: weighted composite
        weights = {
            "D1": 0.08, "D2": 0.07, "D3": 0.06, "D4": 0.08,
            "D5": 0.09, "D6": 0.08, "D7": 0.07, "D8": 0.07,
            "D9": 0.05, "D10": 0.06, "D11": 0.06, "D12": 0.06,
            "D13": 0.06, "D14": 0.07, "D15": 0.05, "D16": 0.04,
        }
        composite = sum(scores[d] * w for d, w in weights.items())
        scores["D17"] = round(composite, 4)

        return scores

    def _weak_dims(self, dim_scores: dict[str, float], threshold: float = 0.72) -> list[str]:
        return [
            f"{d} ({PETRUS_DIMENSIONS[d]}: {v:.2f})"
            for d, v in dim_scores.items()
            if d != "D17" and v < threshold
        ]

    def _refinement_prompt(self, weak_dims: list[str], query: str) -> str:
        """
        Returns a guidance string to feed back to the Oracle
        for the next iteration. Not a block — a nudge.
        """
        if not weak_dims:
            return ""
        lines = [
            "TINA CONFIDENCE REFINEMENT — The following dimensions scored below target:",
            ""
        ]
        for d in weak_dims:
            lines.append(f"  ⚠ {d}")
        lines += [
            "",
            "Guidance for next pass:",
            "- Cite specific sources from the Evidence Ledger where possible.",
            "- Name claims explicitly and match each to documented evidence.",
            "- Avoid inflation language (clearly, obviously, undeniably).",
            "- If registers conflict (legal vs symbolic), separate them clearly.",
            "- Acknowledge alternative interpretations where they exist.",
            "",
            f"Original query: {query}",
            "Please regenerate with these constraints applied.",
        ]
        return "\n".join(lines)

    def process(self, query: str, response: str,
                refine_fn=None) -> ConfidenceReport:
        """
        Main entry point.

        Args:
            query:      The original Oracle query.
            response:   The Oracle's initial response.
            refine_fn:  Optional callable(query, guidance) -> str
                        If provided, the layer will call it to regenerate
                        the response when dimensions are weak.
                        If None, runs scoring only (no LLM refinement).

        Returns:
            ConfidenceReport — always contains the response, never blocks.
        """
        self._log.clear()
        self._stamp(f"TINA Confidence Layer activated")
        self._stamp(f"Query: {query[:80]}...")
        self._stamp(f"Ledger sources: {len(self.ledger)}")

        current_response = response
        initial_scores = self._score_dimensions(current_response, query)
        initial_score = initial_scores["D17"]
        self._stamp(f"Initial D17 score: {initial_score:.4f}")

        refinement_notes = []
        iterations = 0

        # Refinement loop — try to push score up, never block
        if refine_fn and initial_score < self.TARGET:
            for i in range(self.MAX_ITERATIONS):
                dim_scores = self._score_dimensions(current_response, query)
                score = dim_scores["D17"]

                if score >= self.TARGET:
                    self._stamp(f"Target reached at iteration {i+1}: {score:.4f}")
                    break

                weak = self._weak_dims(dim_scores)
                if not weak:
                    break

                self._stamp(f"Iteration {i+1}: score {score:.4f}, weak dims: {len(weak)}")
                guidance = self._refinement_prompt(weak, query)
                refinement_notes.append(f"Pass {i+1}: {len(weak)} weak dimension(s) flagged")

                try:
                    current_response = refine_fn(query, guidance)
                    iterations += 1
                except Exception as e:
                    self._stamp(f"Refinement call failed: {e} — keeping current response")
                    break
        else:
            iterations = 0

        # Final score
        final_scores = self._score_dimensions(current_response, query)
        final_score = final_scores["D17"]
        weak_final = self._weak_dims(final_scores)
        band, color = confidence_band(final_score)

        self._stamp(f"Final D17 score: {final_score:.4f} [{band}]")
        self._stamp(f"Weak dimensions remaining: {len(weak_final)}")

        return ConfidenceReport(
            response=current_response,
            initial_score=initial_score,
            final_score=final_score,
            iterations=iterations,
            band=band,
            band_color=color,
            weak_dimensions=weak_final,
            refinement_notes=refinement_notes,
            audit_trail=list(self._log),
        )


# ── Oracle integration helper ──────────────────────────────────────
def score_oracle_response(query: str, response: str,
                           ledger_sources: Optional[list] = None,
                           ollama_refine: bool = False) -> ConfidenceReport:
    """
    Drop-in function for Oracle Console integration.

    Usage in oracle_engine.py:
        from app.tina_confidence_layer import score_oracle_response
        report = score_oracle_response(query, oracle_text, ledger_sources=sources)
        # report.response is the (possibly refined) text
        # report.band, report.final_score for display
    """
    layer = TINAConfidenceLayer(evidence_ledger=ledger_sources or [])

    refine_fn = None
    if ollama_refine:
        import requests
        def _ollama_refine(q: str, guidance: str) -> str:
            payload = {
                "model": "llama3.2",
                "prompt": f"{guidance}\n\nQuery: {q}",
                "stream": False,
            }
            r = requests.post("http://host.docker.internal:11434/api/generate",
                              json=payload, timeout=60)
            return r.json().get("response", response)
        refine_fn = _ollama_refine

    report = layer.process(query, response, refine_fn=refine_fn)
    report.confidence_tier = tier_from_ledger(ledger_sources or []).value
    return report


# ── Standalone test ────────────────────────────────────────────────
if __name__ == "__main__":
    sample_query = "What does the evidence show about the booking photograph?"
    sample_response = (
        "The evidence clearly shows that defendants published the photograph before conviction. "
        "York v. Story establishes the privacy violation. "
        "The photograph was visible for 1,598 days per documented record."
    )
    sample_ledger = [
        {"label": "york v story", "source_type": "judicial"},
        {"label": "42 usc 1983", "source_type": "statutory"},
        {"label": "complaint filing", "source_type": "public_record"},
    ]

    report = score_oracle_response(sample_query, sample_response, sample_ledger)

    print(f"\n{report.render_label()}")
    print(report.render_weak_dims())
    print(f"\nResponse:\n{report.response}")


# ── Protocol v2.0: Confidence Tier Integration ──────────────────────
from enum import Enum

class ConfidenceTier(str, Enum):
    EXTERNALLY_VERIFIED = "EXTERNALLY_VERIFIED"
    THREE_WITNESS       = "3-WITNESS"
    TWO_WITNESS         = "2-WITNESS"
    SWORN_COMMITTED     = "SWORN_COMMITTED"
    SOURCE_NEEDED       = "SOURCE_NEEDED"
    CLAIMED             = "CLAIMED"

SOURCE_TYPE_TO_TIER = {
    "judicial":       ConfidenceTier.EXTERNALLY_VERIFIED,
    "statutory":      ConfidenceTier.EXTERNALLY_VERIFIED,
    "public_record":  ConfidenceTier.EXTERNALLY_VERIFIED,
    "physical":       ConfidenceTier.THREE_WITNESS,
    "expert_opinion": ConfidenceTier.TWO_WITNESS,
    "document":       ConfidenceTier.TWO_WITNESS,
    "testimony":      ConfidenceTier.SWORN_COMMITTED,
    "digital":        ConfidenceTier.SOURCE_NEEDED,
}

def tier_from_ledger(evidence_ledger: list) -> ConfidenceTier:
    if not evidence_ledger:
        return ConfidenceTier.CLAIMED
    order = list(ConfidenceTier)
    tiers = [SOURCE_TYPE_TO_TIER.get(e.get("source_type", ""), ConfidenceTier.CLAIMED)
             for e in evidence_ledger]
    return min(tiers, key=lambda t: order.index(t))
