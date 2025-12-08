import numpy as np

class QFDEngine:
    """
    Simulates the Axiological Layer: Calculating Utility based on features.
    In a real implementation, this would parse the text. 
    Here we use a simplified heuristic model for demonstration.
    """
    
    @staticmethod
    def calculate_clinical_utility(proposal_text):
        """
        Calculates U_clin based on keywords representing clinical value.
        """
        score = 0.5 # Base satisfaction
        
        # Clinical "Excitement" features
        if "raw" in proposal_text.lower() or "wsi" in proposal_text.lower():
            score += 0.4
        if "ai analysis" in proposal_text.lower():
            score += 0.1
            
        # Penalties (e.g., if delay is mentioned)
        if "delay" in proposal_text.lower() or "latency" in proposal_text.lower():
            score -= 0.2
            
        return min(max(score, 0.0), 1.0)

    @staticmethod
    def calculate_technical_utility(proposal_text):
        """
        Calculates U_tech based on cost and risk keywords.
        """
        score = 0.8 # Base stability
        
        # Technical "Pain" points
        if "500pb" in proposal_text.lower() or "raw storage" in proposal_text.lower():
            score -= 0.7
        if "real-time" in proposal_text.lower() and "huge" in proposal_text.lower():
            score -= 0.5
            
        # Mitigations (Technical wins)
        if "cold storage" in proposal_text.lower() or "tiered" in proposal_text.lower():
            score += 0.4
        if "jpeg" in proposal_text.lower() or "compressed" in proposal_text.lower():
            score += 0.3

        return min(max(score, 0.0), 1.0)

    @staticmethod
    def calculate_nash_product(u_clin, u_tech):
        return u_clin * u_tech
