# src/engine.py
import math

class AxiologicalEngine:
    """
    Implements the mathematical logic for Utility Calculation and Nash Bargaining Solution.
    Ref: Layer 2 in Architecture
    """

    def __init__(self, budget_max: float = 100000.0, ambiguity_penalty_coeff: float = 0.2):
        self.budget_max = budget_max
        self.lambda_ambiguity = ambiguity_penalty_coeff  # Lambda in Eq 1
        self.risk_weight = 10000.0 # Beta coefficient for risk monetization

    def calculate_clinical_utility(self, importance_weight: int, satisfaction: float, ambiguity_score: float) -> float:
        """
        Calculates U_clin based on QFD weights and Ambiguity Penalty.
        Formula: U_clin = (w * phi(r)) - lambda * Psi(R)
        """
        # Normalize inputs
        w_norm = importance_weight / 5.0  # Assuming 1-5 scale
        
        # Core utility
        u_base = w_norm * satisfaction
        
        # Penalty
        penalty = self.lambda_ambiguity * ambiguity_score
        
        return max(0.0, u_base - penalty)

    def calculate_technical_utility(self, est_cost: float, risk_prob: float) -> float:
        """
        Calculates U_tech based on Budget, Cost, and Risk.
        Formula: U_tech = Budget_max - (Cost + beta * Risk)
        Note: We normalize this to 0-1 range for Nash calculation.
        """
        total_impact = est_cost + (self.risk_weight * risk_prob)
        
        # Calculating remaining budget ratio as utility
        if total_impact > self.budget_max:
            return 0.1  # Soft floor for rejection
        
        utility = (self.budget_max - total_impact) / self.budget_max
        return max(0.1, utility)

    def calculate_nash_product(self, u_clin: float, u_tech: float, d_clin: float = 0.0, d_tech: float = 0.0) -> float:
        """
        Calculates the Nash Product to measure 'fairness'.
        Formula: Omega = (U_clin - d_clin) * (U_tech - d_tech)
        """
        surplus_clin = max(0, u_clin - d_clin)
        surplus_tech = max(0, u_tech - d_tech)
        
        return surplus_clin * surplus_tech