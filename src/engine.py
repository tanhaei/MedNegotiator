from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from src.guard import ConsistencyGuard
from src.utils import clamp


class AxiologicalEngine:
    """
    Reference implementation of the paper's utility logic.
    Utilities are normalized to [0, 1] so the Nash product is interpretable.
    """

    def __init__(
        self,
        budget_max: float = 100000.0,
        ambiguity_penalty_coeff: float = 0.5,
        beta_risk: float = 0.3,
        technical_acceptance_threshold: float = 0.25,
        guard: Optional[ConsistencyGuard] = None,
    ) -> None:
        self.budget_max = budget_max
        self.lambda_ambiguity = ambiguity_penalty_coeff
        self.beta_risk = beta_risk
        self.technical_acceptance_threshold = technical_acceptance_threshold
        self.guard = guard or ConsistencyGuard(budget_max=budget_max)

    def calculate_clinical_utility(
        self,
        importance_weight: int,
        satisfaction: float,
        ambiguity_score: float,
    ) -> float:
        """
        Normalized form of U_clin = sum(w_i * phi(r_i)) - lambda * Psi(R)
        for a single candidate requirement bundle.
        """
        w_norm = clamp(importance_weight / 5.0)
        phi_score = clamp(satisfaction)
        psi_score = clamp(ambiguity_score)
        return clamp((w_norm * phi_score) - (self.lambda_ambiguity * psi_score))

    def calculate_technical_utility(
        self,
        est_cost: float,
        risk_prob: float,
        coupling_penalty: float = 0.0,
    ) -> float:
        """
        Normalized variant of the paper's technical utility:
        U_tech = Budget_max - (Cost + beta * Risk), then mapped to [0, 1].
        """
        cost_ratio = max(est_cost, 0.0) / self.budget_max
        risk_term = self.beta_risk * clamp(risk_prob)
        return clamp(1.0 - cost_ratio - risk_term - clamp(coupling_penalty))

    def calculate_nash_product(
        self,
        u_clin: float,
        u_tech: float,
        d_clin: float = 0.0,
        d_tech: float = 0.0,
    ) -> float:
        surplus_clin = max(0.0, u_clin - d_clin)
        surplus_tech = max(0.0, u_tech - d_tech)
        return surplus_clin * surplus_tech

    def calculate_joint_utility(
        self,
        u_clin: float,
        u_tech: float,
        hard_violations: Iterable[str],
        d_clin: float = 0.0,
        d_tech: float = 0.0,
    ) -> float:
        violations = list(hard_violations)
        if violations:
            return float("-inf")
        return self.calculate_nash_product(u_clin, u_tech, d_clin=d_clin, d_tech=d_tech)

    def should_accept(self, u_tech: float, joint_utility: float, hard_violations: List[str]) -> bool:
        return not hard_violations and u_tech >= self.technical_acceptance_threshold and joint_utility > 0.0

    def summarize_metrics(
        self,
        importance_weight: int,
        satisfaction: float,
        ambiguity_score: float,
        est_cost: float,
        risk_prob: float,
        hard_violations: List[str],
    ) -> Dict[str, float]:
        u_clin = self.calculate_clinical_utility(importance_weight, satisfaction, ambiguity_score)
        u_tech = self.calculate_technical_utility(est_cost, risk_prob)
        joint = self.calculate_joint_utility(u_clin, u_tech, hard_violations)
        return {
            "u_clin": u_clin,
            "u_tech": u_tech,
            "nash_product": 0.0 if joint == float("-inf") else joint,
        }
