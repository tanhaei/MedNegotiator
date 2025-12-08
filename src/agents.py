from openai import OpenAI
import os

class BaseAgent:
    def __init__(self, name, role, system_prompt):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        # Initialize OpenAI client (Assumes API Key is in env)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.history = [{"role": "system", "content": system_prompt}]

    def generate_response(self, opponent_input):
        self.history.append({"role": "user", "content": opponent_input})
        
        # In a real scenario, we would use the LLM call here.
        # response = self.client.chat.completions.create(model="gpt-4", messages=self.history)
        # content = response.choices[0].message.content
        
        # For this demo repo (to be runnable without credits), we simulate the logic 
        # based on the paper's script, but the structure is ready for LLM.
        return f"[LLM GENERATION Placeholder for {self.name}]" 

class ClinicalAgent(BaseAgent):
    def __init__(self):
        prompt = """
        You are Dr. AI, a senior pathologist with 20 years of experience.
        BIAS: Severity Bias (Prioritize patient data completeness over cost).
        GOAL: Ensure raw WSI files are stored for AI research.
        """
        super().__init__("Dr. Onc", "Clinical Agent", prompt)
    
    # Override for simulation purposes if no API key
    def simulate_response(self, round_num, context):
        if round_num == 1:
            return "I propose REQ-042. We need raw .SVS files. Lossy compression destroys nuclear details essential for diagnosis."
        elif round_num == 3:
            return "Acceptable, provided the retrieval process is automated and SLA is reasonable."
        return "I insist on data quality."

class TechnicalAgent(BaseAgent):
    def __init__(self):
        prompt = """
        You are Arch. Sys, a pragmatic software architect.
        BIAS: Loss Aversion (Risk avoidance, budget conscious).
        GOAL: Maintain system stability and stay within the $50k/mo budget.
        """
        super().__init__("Arch. Sys", "Technical Agent", prompt)

    def simulate_response(self, round_num, context):
        if round_num == 1:
            return "Rejected. Storing 500PB of hot data costs $10M/year. This violates our budget constraints."
        elif round_num == 2:
            return "I acknowledge the value, but the infrastructure can't handle it. I propose storing downsampled JPEGs and discarding raw files."
        elif round_num == 3:
            return "Acceptable. Cold storage fits within the budget margin."
        return "We need to cut costs."

class MediatorAgent(BaseAgent):
    def __init__(self):
        prompt = "You are the Mediator. Your goal is to maximize the Nash Product of the negotiation."
        super().__init__("Mediator", "Conflict Resolver", prompt)
        
    def propose_solution(self):
        return "Suggesting Hybrid Architecture: 1. Hot Storage for Tiles (View). 2. Cold Storage for Raw (Archive). This balances Cost and Value."
