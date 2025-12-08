# src/protocol.py
from src.agents import ClinicalAgent, TechnicalAgent, MediatorAgent
from src.engine import AxiologicalEngine

class NegotiationProtocol:
    """
    Manages the Dynamic Negotiation Protocol (Round-based state machine).
    Ref: Layer 3 and Section 3.4 [cite: 90, 126]
    """
    
    def __init__(self, scenario: str, max_rounds: int = 5):
        self.scenario = scenario
        self.max_rounds = max_rounds
        self.engine = AxiologicalEngine()
        self.logs = []

    def run(self, clin_agent: ClinicalAgent, tech_agent: TechnicalAgent, mediator: MediatorAgent):
        current_proposal = None
        
        print(f"--- Starting Negotiation for Scenario: {self.scenario} ---")

        for round_num in range(1, self.max_rounds + 1):
            print(f"\n[Round {round_num}]")
            
            # Phase 1: Clinical Agent Proposes [cite: 127]
            if round_num == 1 or not current_proposal:
                proposal_data = clin_agent.propose(self.scenario)
                print(f"Dr. AI proposes: {proposal_data.get('text')}")
                print(f"Rationale: {proposal_data.get('rationale')}")
            
            # Phase 2: Technical Agent Evaluates (Axiological Check) [cite: 129]
            tech_eval = tech_agent.evaluate(proposal_data)
            
            # Calculate Utilities using the Engine
            u_clin = self.engine.calculate_clinical_utility(
                importance_weight=proposal_data.get('importance_1_to_5', 5),
                satisfaction=0.9, # Assumed high for their own proposal
                ambiguity_score=0.1
            )
            u_tech = self.engine.calculate_technical_utility(
                est_cost=tech_eval.get('estimated_cost', 100000),
                risk_prob=tech_eval.get('risk_prob', 0.5)
            )
            
            nash_score = self.engine.calculate_nash_product(u_clin, u_tech)
            print(f"[System] U_clin: {u_clin:.2f}, U_tech: {u_tech:.2f} -> Nash: {nash_score:.2f}")

            # Check for Consensus
            if tech_eval.get('accepted_bool') and nash_score > 0.5:
                print(">>> CONSENSUS REACHED <<<")
                return self._generate_output(proposal_data, tech_eval)

            # Phase 3: Critique & Counter-Offer (Deadlock Handling)
            print(f"Arch. AI rejects: {tech_eval.get('critique_text')}")
            
            # Deadlock Logic [cite: 135]
            if round_num >= 3 and nash_score < 0.2:
                print(">>> DEADLOCK DETECTED - ACTIVATING MEDIATOR <<<")
                resolution = mediator.resolve_deadlock(clin_agent.history, tech_agent.history)
                print(f"Mediator Resolution: {resolution}")
                return resolution

            # Loop continues (Responder becomes proposer in full implementation)
            
        print(">>> MAX ROUNDS REACHED - NO AGREEMENT <<<")
        return None

    def _generate_output(self, final_proposal, final_tech_review):
        # Generates JSON/SRS artifact [cite: 147]
        return {
            "status": "AGREED",
            "requirement": final_proposal['text'],
            "constraints": final_tech_review['critique_text']
        }