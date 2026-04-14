from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.agents import ClinicalAgent, MediatorAgent, TechnicalAgent
from src.engine import AxiologicalEngine


class NegotiationProtocol:
    """
    Alternating-offers protocol with guardrails, deadlock detection, and mediator fallback.
    """

    def __init__(
        self,
        scenario: str,
        max_rounds: int = 6,
        deadlock_patience: int = 2,
        deadlock_delta: float = 0.03,
        engine: Optional[AxiologicalEngine] = None,
    ) -> None:
        self.scenario = scenario
        self.max_rounds = max_rounds
        self.deadlock_patience = deadlock_patience
        self.deadlock_delta = deadlock_delta
        self.engine = engine or AxiologicalEngine()
        self.logs: List[Dict[str, Any]] = []
        self.stabilized_predicates: List[str] = []

    def run(
        self,
        clin_agent: ClinicalAgent,
        tech_agent: TechnicalAgent,
        mediator: MediatorAgent,
    ) -> Dict[str, Any]:
        proposal = clin_agent.propose(self.scenario)
        proposer: str = "clinical"
        score_history: List[float] = []

        for round_num in range(1, self.max_rounds + 1):
            evaluation = tech_agent.evaluate(proposal)
            guard_report = self.engine.guard.check(
                proposal_text=proposal["text"],
                scenario=self.scenario,
                stabilized_predicates=self.stabilized_predicates,
                estimated_cost=evaluation["estimated_cost"],
                risk_prob=evaluation["risk_prob"],
            )
            hard_violations = list(evaluation.get("hard_violations", [])) + list(guard_report.get("violations", []))

            metrics = self.engine.summarize_metrics(
                importance_weight=int(proposal.get("importance_1_to_5", 5)),
                satisfaction=float(proposal.get("satisfaction", 0.90)),
                ambiguity_score=float(proposal.get("ambiguity_score", 0.10)),
                est_cost=float(evaluation["estimated_cost"]),
                risk_prob=float(evaluation["risk_prob"]),
                hard_violations=hard_violations,
            )
            accepted = self.engine.should_accept(metrics["u_tech"], metrics["nash_product"], hard_violations)
            accepted = accepted and bool(evaluation.get("accepted_bool", False))

            log_entry = {
                "round": round_num,
                "proposer": proposer,
                "proposal": proposal,
                "technical_review": evaluation,
                "guard": guard_report,
                **metrics,
                "hard_violations": hard_violations,
                "accepted": accepted,
            }
            self.logs.append(log_entry)
            score_history.append(metrics["nash_product"])

            if accepted:
                self.stabilized_predicates = list(guard_report.get("predicates", []))
                return self._generate_output(status="AGREED", final_log=log_entry, mediated=False)

            if self._deadlock_detected(score_history):
                mediated = self._run_mediator(mediator, tech_agent, proposal, evaluation.get("critique_text", ""))
                if mediated is not None:
                    return mediated

            proposal = tech_agent.counter_offer(proposal, evaluation)
            proposer = "technical" if proposer == "clinical" else "clinical"

        return self._generate_output(status="NO_AGREEMENT", final_log=self.logs[-1] if self.logs else {}, mediated=False)

    def _deadlock_detected(self, scores: List[float]) -> bool:
        if len(scores) < self.deadlock_patience + 1:
            return False
        recent = scores[-(self.deadlock_patience + 1) :]
        deltas = [abs(recent[idx + 1] - recent[idx]) for idx in range(len(recent) - 1)]
        return all(delta <= self.deadlock_delta for delta in deltas)

    def _run_mediator(
        self,
        mediator: MediatorAgent,
        tech_agent: TechnicalAgent,
        proposal: Dict[str, Any],
        critique: str,
    ) -> Optional[Dict[str, Any]]:
        best_result: Optional[Tuple[float, Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, float]]] = None

        for candidate in mediator.generate_candidate_variants(proposal, critique):
            evaluation = tech_agent.evaluate(candidate)
            guard_report = self.engine.guard.check(
                proposal_text=candidate["text"],
                scenario=self.scenario,
                stabilized_predicates=self.stabilized_predicates,
                estimated_cost=evaluation["estimated_cost"],
                risk_prob=evaluation["risk_prob"],
            )
            hard_violations = list(evaluation.get("hard_violations", [])) + list(guard_report.get("violations", []))
            metrics = self.engine.summarize_metrics(
                importance_weight=int(candidate.get("importance_1_to_5", 5)),
                satisfaction=float(candidate.get("satisfaction", 0.90)),
                ambiguity_score=float(candidate.get("ambiguity_score", 0.10)),
                est_cost=float(evaluation["estimated_cost"]),
                risk_prob=float(evaluation["risk_prob"]),
                hard_violations=hard_violations,
            )
            if hard_violations:
                continue
            score = metrics["nash_product"]
            if best_result is None or score > best_result[0]:
                best_result = (score, candidate, evaluation, guard_report, metrics)

        if best_result is None:
            return None

        _, candidate, evaluation, guard_report, metrics = best_result
        accepted = self.engine.should_accept(metrics["u_tech"], metrics["nash_product"], [])
        if not accepted:
            return None

        log_entry = {
            "round": len(self.logs) + 1,
            "proposer": "mediator",
            "proposal": candidate,
            "technical_review": evaluation,
            "guard": guard_report,
            **metrics,
            "hard_violations": [],
            "accepted": True,
        }
        self.logs.append(log_entry)
        self.stabilized_predicates = list(guard_report.get("predicates", []))
        return self._generate_output(status="AGREED", final_log=log_entry, mediated=True)

    def _generate_output(self, status: str, final_log: Dict[str, Any], mediated: bool) -> Dict[str, Any]:
        proposal = final_log.get("proposal", {})
        review = final_log.get("technical_review", {})
        return {
            "status": status,
            "mediated": mediated,
            "scenario": self.scenario,
            "requirement": proposal.get("text"),
            "rationale": proposal.get("rationale"),
            "technical_constraints": review.get("critique_text"),
            "metrics": {
                "u_clin": round(float(final_log.get("u_clin", 0.0)), 4),
                "u_tech": round(float(final_log.get("u_tech", 0.0)), 4),
                "nash_product": round(float(final_log.get("nash_product", 0.0)), 4),
                "anchor_score": round(float(final_log.get("guard", {}).get("anchor_score", 0.0)), 4),
                "estimated_cost": round(float(review.get("estimated_cost", 0.0)), 2),
                "risk_prob": round(float(review.get("risk_prob", 0.0)), 4),
            },
            "guard": {
                "predicates": final_log.get("guard", {}).get("predicates", []),
                "warnings": final_log.get("guard", {}).get("warnings", []),
                "violations": final_log.get("hard_violations", []),
            },
            "negotiation_trace": self.logs,
        }
