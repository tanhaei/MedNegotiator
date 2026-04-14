from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional runtime dependency
    OpenAI = Any  # type: ignore

from src.utils import clamp, extract_json_object, unique_preserve_order


class BaseAgent:
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        client: Optional[OpenAI] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
    ) -> None:
        self.name = name
        self.role = role
        self.goal = goal
        self.client = client
        self.model_name = model_name or os.getenv("MODEL_NAME", "gpt-4o")
        self.temperature = temperature
        self.history: List[Dict[str, str]] = []

    def _call_llm_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if self.client is None:
            return {}

        messages = [
            {"role": "system", "content": system_prompt},
            *self.history,
            {"role": "user", "content": user_prompt},
        ]
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        parsed = extract_json_object(content)
        self.history.append({"role": "assistant", "content": content})
        return parsed

    def retrieve_context(self, query: str, domain: str) -> str:
        """
        Placeholder RAG adapter. In the paper this is backed by FAISS/vector search.
        Here it stays deterministic but exposes where grounding would be attached.
        """
        return f"[{domain} RAG context for: {query}]"


class ClinicalAgent(BaseAgent):
    def propose(self, scenario: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        rag_data = self.retrieve_context(scenario, domain="clinical")
        sys_prompt = (
            f"You are {self.name}, a {self.role}. Goal: {self.goal}. "
            "Bias: Severity Bias. Prioritize patient safety and clinical value. "
            "Return valid JSON with keys: text, importance_1_to_5, satisfaction, ambiguity_score, rationale."
        )
        user_prompt = (
            f"Scenario: {scenario}\nClinical context: {rag_data}\n"
            f"Feedback to address: {feedback or 'None'}"
        )
        parsed = self._call_llm_json(sys_prompt, user_prompt)
        if parsed:
            return self._finalize_proposal(parsed, scenario, feedback)
        return self._fallback_proposal(scenario, feedback)

    def critique(self, proposal_text: str) -> Dict[str, str]:
        return {
            "text": "Clinical review prefers preserving clinically relevant detail, clinician visibility, and safety-oriented fallback behavior."
        }

    def _fallback_proposal(self, scenario: str, feedback: Optional[str]) -> Dict[str, Any]:
        lowered = scenario.lower()
        importance = 5
        satisfaction = 0.95
        ambiguity = 0.18 if any(word in lowered for word in ("real-time", "fast", "low latency")) else 0.10

        text = (
            "The system shall provide an AI-assisted ICU dashboard for Heart Rate and SpO2 with continuous monitoring, "
            "bedside visibility for clinicians, and immediate alerting for abnormal trends."
        )
        if "1ms" in lowered:
            text += " The dashboard shall target 1 ms end-to-end latency for critical bedside updates."
        elif "ms" in lowered:
            latency_phrase = re.search(r"\d+(?:\.\d+)?\s*ms", scenario, flags=re.IGNORECASE)
            if latency_phrase:
                text += f" The dashboard shall target {latency_phrase.group(0)} latency for critical bedside updates."

        if feedback:
            text += f" Revised to address feedback: {feedback}."
            ambiguity = max(0.05, ambiguity - 0.05)

        proposal = {
            "text": text,
            "importance_1_to_5": importance,
            "satisfaction": satisfaction,
            "ambiguity_score": clamp(ambiguity),
            "rationale": "Prioritizes patient safety, continuous monitoring, and rapid clinical response.",
        }
        self.history.append({"role": "assistant", "content": json.dumps(proposal)})
        return proposal

    def _finalize_proposal(self, proposal: Dict[str, Any], scenario: str, feedback: Optional[str]) -> Dict[str, Any]:
        proposal.setdefault("text", scenario)
        proposal["importance_1_to_5"] = int(proposal.get("importance_1_to_5", 5))
        proposal["satisfaction"] = clamp(float(proposal.get("satisfaction", 0.90)))
        proposal["ambiguity_score"] = clamp(float(proposal.get("ambiguity_score", 0.10)))
        proposal.setdefault("rationale", "Clinically grounded requirement.")
        if feedback:
            proposal["rationale"] += f" Updated using feedback: {feedback}"
        return proposal


class TechnicalAgent(BaseAgent):
    def evaluate(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        rag_data = self.retrieve_context(proposal["text"], domain="technical")
        sys_prompt = (
            f"You are {self.name}, a {self.role}. Goal: {self.goal}. "
            "Bias: Loss Aversion. Return valid JSON with keys: critique_text, infra_cost, effort_cost, "
            "estimated_cost, risk_prob, accepted_bool, hard_violations."
        )
        user_prompt = f"Proposal: {proposal['text']}\nTechnical context: {rag_data}"
        parsed = self._call_llm_json(sys_prompt, user_prompt)
        if parsed:
            return self._finalize_evaluation(parsed)
        return self._fallback_evaluation(proposal)

    def counter_offer(self, proposal: Dict[str, Any], evaluation: Dict[str, Any]) -> Dict[str, Any]:
        critique = evaluation.get("critique_text", "")
        base_text = proposal["text"]
        lowered = base_text.lower()

        revised_text = base_text
        rationale_parts = [
            "Introduces a technical compromise to preserve clinical value while lowering cost and risk."
        ]

        if "1 ms" in lowered or "1ms" in lowered or "latency_sub_1ms" in evaluation.get("technical_flags", []):
            revised_text = re.sub(r"1\s*ms", "200 ms", revised_text, flags=re.IGNORECASE)
            revised_text += " Use edge caching for bedside rendering and asynchronous analytics for non-critical computations."
            rationale_parts.append("Replaces an unrealistic 1 ms target with a safer sub-200 ms bedside goal.")

        if any(flag in critique.lower() for flag in ("budget", "cost", "overrun")) and all(token not in revised_text.lower() for token in ("tiered storage", "tiered-storage", "archive")):
            revised_text += " Persist clinically hot data in fast storage and archive bulk historical data using a tiered-storage policy."
            rationale_parts.append("Adds tiered storage to reduce infrastructure cost.")

        if all(token not in revised_text.lower() for token in ("audit", "encryption", "override")) and ("patient" in lowered or "icu" in lowered or "ai" in lowered):
            revised_text += " Include audit logging, encryption in transit, and clinician override for high-risk alerts."
            rationale_parts.append("Adds governance controls required by the paper's safety guardrails.")

        counter = {
            "text": revised_text,
            "importance_1_to_5": max(3, int(proposal.get("importance_1_to_5", 5)) - 1),
            "satisfaction": clamp(float(proposal.get("satisfaction", 0.90)) - 0.08),
            "ambiguity_score": clamp(float(proposal.get("ambiguity_score", 0.10)) - 0.05),
            "rationale": " ".join(unique_preserve_order(rationale_parts)),
        }
        self.history.append({"role": "assistant", "content": json.dumps(counter)})
        return counter

    def _fallback_evaluation(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        text = proposal["text"].lower()
        infra_cost = 15000.0
        effort_cost = 10000.0
        risk_prob = 0.20
        critique_parts: List[str] = []
        technical_flags: List[str] = []
        hard_violations: List[str] = []

        if "dashboard" in text or "monitor" in text or "vitals" in text:
            infra_cost += 15000.0
            effort_cost += 12000.0
            risk_prob += 0.10
            technical_flags.append("real_time_dashboard")

        if "ai" in text:
            infra_cost += 8000.0
            effort_cost += 9000.0
            risk_prob += 0.08
            technical_flags.append("ai_component")

        latency_match = re.search(r"(\d+(?:\.\d+)?)\s*ms", text)
        if latency_match:
            latency_ms = float(latency_match.group(1))
            if latency_ms <= 1:
                infra_cost += 35000.0
                effort_cost += 25000.0
                risk_prob += 0.38
                critique_parts.append("1 ms latency target is operationally unrealistic for a hospital workflow and sharply increases risk.")
                technical_flags.append("latency_sub_1ms")
            elif latency_ms <= 100:
                infra_cost += 12000.0
                effort_cost += 10000.0
                risk_prob += 0.18
                critique_parts.append("Very aggressive latency target increases engineering complexity.")
                technical_flags.append("latency_sub_100ms")
            elif latency_ms <= 200:
                infra_cost += 5000.0
                effort_cost += 5000.0
                risk_prob += 0.05
                technical_flags.append("latency_sub_200ms")

        if "edge caching" in text or "cache" in text:
            infra_cost -= 5000.0
            risk_prob -= 0.05
            critique_parts.append("Caching reduces bedside rendering latency.")

        if "asynchronous" in text or "async" in text:
            effort_cost -= 3000.0
            risk_prob -= 0.05
            critique_parts.append("Asynchronous processing reduces critical-path pressure.")

        if "tiered-storage" in text or "tiered storage" in text or "archive" in text:
            infra_cost -= 8000.0
            risk_prob -= 0.03
            critique_parts.append("Tiered storage lowers long-term infrastructure cost.")

        if "audit" in text or "encryption" in text or "override" in text:
            effort_cost += 3000.0
            risk_prob -= 0.08
            critique_parts.append("Governance controls reduce safety and compliance exposure.")

        estimated_cost = max(0.0, infra_cost + effort_cost)
        risk_prob = clamp(risk_prob)
        if estimated_cost > 100000.0:
            hard_violations.append("Budget overrun")
            critique_parts.append("Projected cost exceeds budget ceiling.")
        if risk_prob > 0.80:
            hard_violations.append("Excessive technical risk")
            critique_parts.append("Risk remains above acceptable threshold.")

        evaluation = {
            "critique_text": " ".join(unique_preserve_order(critique_parts))
            or "Proposal is technically feasible.",
            "infra_cost": round(infra_cost, 2),
            "effort_cost": round(effort_cost, 2),
            "estimated_cost": round(estimated_cost, 2),
            "risk_prob": round(risk_prob, 3),
            "accepted_bool": len(hard_violations) == 0 and estimated_cost <= 85000.0 and risk_prob <= 0.55,
            "hard_violations": hard_violations,
            "technical_flags": technical_flags,
        }
        self.history.append({"role": "assistant", "content": json.dumps(evaluation)})
        return evaluation

    def _finalize_evaluation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        evaluation.setdefault("critique_text", "Technical review completed.")
        evaluation["infra_cost"] = float(evaluation.get("infra_cost", 0.0))
        evaluation["effort_cost"] = float(evaluation.get("effort_cost", 0.0))
        evaluation["estimated_cost"] = float(evaluation.get("estimated_cost", evaluation["infra_cost"] + evaluation["effort_cost"]))
        evaluation["risk_prob"] = clamp(float(evaluation.get("risk_prob", 0.4)))
        evaluation["accepted_bool"] = bool(evaluation.get("accepted_bool", False))
        evaluation["hard_violations"] = list(evaluation.get("hard_violations", []))
        evaluation["technical_flags"] = list(evaluation.get("technical_flags", []))
        return evaluation


class MediatorAgent(BaseAgent):
    def generate_candidate_variants(self, proposal: Dict[str, Any], critique: str) -> List[Dict[str, Any]]:
        base_text = proposal["text"]
        candidates: List[Dict[str, Any]] = []

        variants = [
            base_text + " Adopt a hybrid architecture with edge caching for bedside views and asynchronous analytics for non-critical computations.",
            base_text + " Replace always-hot storage with tiered storage: hot operational data plus cold archival retention.",
            base_text + " Add clinician override, audit logging, and encryption while relaxing the strict latency target to a clinically safe sub-200 ms threshold.",
            base_text + " Use event-driven alerts for critical vitals, keep explanatory AI outputs asynchronous, and preserve traceability through audit logs.",
        ]

        for variant in unique_preserve_order(variants):
            candidates.append(
                {
                    "text": variant,
                    "importance_1_to_5": max(3, int(proposal.get("importance_1_to_5", 5)) - 1),
                    "satisfaction": clamp(float(proposal.get("satisfaction", 0.90)) - 0.05),
                    "ambiguity_score": clamp(float(proposal.get("ambiguity_score", 0.10)) - 0.05),
                    "rationale": (
                        "Mediator-generated compromise chosen from a population of hybrid/tiered variants to maximize the Nash product "
                        "while preserving safety and feasibility."
                    ),
                }
            )
        self.history.append({"role": "assistant", "content": json.dumps({"critique": critique, "candidates": candidates})})
        return candidates
