from __future__ import annotations

import re
from typing import Dict, List, Optional

from src.utils import cosine_token_similarity, unique_preserve_order


class ConsistencyGuard:
    """
    Lightweight NL -> predicate -> rule check inspired by the paper's Consistency Guard.
    It is intentionally deterministic so the demo remains reproducible offline.
    """

    def __init__(self, drift_threshold: float = 0.85, budget_max: float = 100000.0, max_risk: float = 0.80):
        self.drift_threshold = drift_threshold
        self.budget_max = budget_max
        self.max_risk = max_risk

    def extract_predicates(self, text: str) -> List[str]:
        lowered = text.lower()
        predicates: List[str] = []

        keyword_map = {
            "real_time_monitoring": ["real-time", "realtime", "continuous", "streaming"],
            "ai_decision_support": ["ai", "ml", "predictive", "decision support"],
            "patient_data": ["patient", "icu", "ehr", "phi", "vitals", "spo2", "heart rate"],
            "raw_storage": ["raw", "svs", "wsi", "full-resolution", "hot storage"],
            "tiered_storage": ["tiered storage", "cold storage", "archive", "archival", "glacier"],
            "hybrid_architecture": ["hybrid", "edge cache", "edge caching", "cache", "async", "asynchronous"],
            "audit_logging": ["audit", "traceability", "logging", "access log"],
            "human_review": ["human review", "clinician override", "human-in-the-loop", "pharmacist verification"],
            "encryption": ["encrypt", "encrypted", "tls", "access control", "rbac"],
        }

        for predicate, markers in keyword_map.items():
            if any(marker in lowered for marker in markers):
                predicates.append(predicate)

        latency_match = re.search(r"(\d+(?:\.\d+)?)\s*ms", lowered)
        if latency_match:
            latency_ms = float(latency_match.group(1))
            if latency_ms <= 1:
                predicates.append("latency_sub_1ms")
            elif latency_ms <= 100:
                predicates.append("latency_sub_100ms")
            elif latency_ms <= 200:
                predicates.append("latency_sub_200ms")
        return unique_preserve_order(predicates)

    def check(
        self,
        proposal_text: str,
        scenario: str,
        stabilized_predicates: Optional[List[str]] = None,
        estimated_cost: Optional[float] = None,
        risk_prob: Optional[float] = None,
    ) -> Dict[str, object]:
        stabilized_predicates = stabilized_predicates or []
        predicates = self.extract_predicates(proposal_text)
        anchor_score = cosine_token_similarity(proposal_text, scenario)

        violations: List[str] = []
        warnings: List[str] = []

        # Rule 1: Guard against semantic drift. For counter-offers we tolerate lower
        # alignment when the proposal still carries a compromise architecture pattern.
        has_compromise_pattern = any(
            predicate in predicates for predicate in ("tiered_storage", "hybrid_architecture", "human_review")
        )
        if anchor_score < self.drift_threshold and not has_compromise_pattern:
            violations.append("Semantic drift detected (anchor score below threshold).")
        elif anchor_score < self.drift_threshold:
            warnings.append("Anchor score below threshold, but acceptable after compromise pattern injection.")

        # Rule 2: Equivalent to not (RawStorage and BudgetOverrun)
        if estimated_cost is not None and estimated_cost > self.budget_max and "raw_storage" in predicates:
            violations.append("Hard rule violated: Raw high-granularity storage cannot coexist with budget overrun.")

        # Rule 3: Unrealistic safety-critical latency promise under high risk
        if risk_prob is not None and risk_prob > self.max_risk and "latency_sub_1ms" in predicates:
            violations.append("Hard rule violated: sub-1ms latency promise is unsafe under current technical risk.")

        # Rule 4: Patient-facing AI should include governance controls.
        if "ai_decision_support" in predicates and "patient_data" in predicates:
            has_governance = any(predicate in predicates for predicate in ("audit_logging", "human_review", "encryption"))
            if not has_governance:
                warnings.append("Proposal lacks explicit governance controls (audit logging, encryption, or human review).")

        # Rule 5: Do not contradict stabilized compromise patterns.
        if "tiered_storage" in stabilized_predicates and "raw_storage" in predicates and "tiered_storage" not in predicates:
            violations.append("Proposal conflicts with previously stabilized tiered-storage compromise.")

        return {
            "ok": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "anchor_score": anchor_score,
            "predicates": predicates,
        }
