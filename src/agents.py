# src/agents.py
import openai
import json
from typing import Dict, List

class BaseAgent:
    def __init__(self, name: str, role: str, goal: str, client: openai.OpenAI):
        self.name = name
        self.role = role
        self.goal = goal
        self.client = client
        self.history = []

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        messages = [{"role": "system", "content": system_prompt}] + self.history + [{"role": "user", "content": user_prompt}]
        response = self.client.chat.completions.create(
            model="gpt-4", # Or suitable model
            messages=messages,
            temperature=0.2 # Low temp for reproducibility [cite: 283]
        )
        return response.choices[0].message.content

    def retrieve_context(self, query: str) -> str:
        """
        Mock RAG Stub. In production, this connects to a Vector DB.
        Ref: Layer 1 RAG Knowledge Base [cite: 81]
        """
        # This acts as a placeholder for the RAG retrieval logic described in Section 3.1.1
        return f"[Retrieved Context: Guidelines relevant to '{query}']"

class ClinicalAgent(BaseAgent):
    """
    Represents the Demand Side (Dr. AI).
    Bias: Severity Bias (Over-prioritizes patient safety/data granularity). [cite: 98]
    """
    def propose(self, scenario: str) -> Dict:
        rag_data = self.retrieve_context(scenario)
        sys_prompt = f"""
        You are {self.name}, a {self.role}. Your goal is: {self.goal}.
        You have 'Severity Bias': You prioritize clinical detail/safety over cost.
        Context: {rag_data}
        Task: Propose a requirement for the scenario: '{scenario}'.
        Output format: JSON with keys 'text', 'importance_1_to_5', 'rationale'.
        """
        response = self._call_llm(sys_prompt, "Generate proposal.")
        self.history.append({"role": "assistant", "content": response})
        return self._parse_json(response)

    def critique(self, proposal_text: str) -> Dict:
        sys_prompt = f"You are {self.name}. Critique the technical proposal regarding '{proposal_text}'. Focus on patient safety."
        response = self._call_llm(sys_prompt, "Evaluate this proposal.")
        return {"text": response}

    def _parse_json(self, text):
        # Simplified parser for demo
        try:
            return json.loads(text)
        except:
            return {"text": text, "importance_1_to_5": 5, "rationale": "Parsing error"}

class TechnicalAgent(BaseAgent):
    """
    Represents the Supply Side (Arch. AI).
    Bias: Loss Aversion (Prioritizes stability/budget over features). [cite: 103]
    """
    def evaluate(self, proposal: Dict) -> Dict:
        rag_data = self.retrieve_context("infrastructure constraints")
        sys_prompt = f"""
        You are {self.name}, a {self.role}. Your goal is: {self.goal}.
        You have 'Loss Aversion': You reject risks and high costs.
        Context: {rag_data}
        Task: Evaluate the clinical proposal: '{proposal['text']}'.
        Estimate cost ($) and risk probability (0.0-1.0).
        Output format: JSON with keys 'critique_text', 'estimated_cost', 'risk_prob', 'accepted_bool'.
        """
        response = self._call_llm(sys_prompt, "Evaluate proposal.")
        self.history.append({"role": "assistant", "content": response})
        return self._parse_json(response)

    def counter_offer(self, clinical_demand: str) -> Dict:
        sys_prompt = f"You are {self.name}. Offer a technical compromise for: '{clinical_demand}' that saves cost."
        response = self._call_llm(sys_prompt, "Generate counter-offer.")
        return {"text": response}
    
    def _parse_json(self, text):
        try:
            return json.loads(text)
        except:
            return {"critique_text": text, "estimated_cost": 50000, "risk_prob": 0.5, "accepted_bool": False}

class MediatorAgent(BaseAgent):
    """
    Ref: Section 3.5 Conflict Resolution via Mediator Agent [cite: 135]
    """
    def resolve_deadlock(self, clin_history, tech_history) -> str:
        sys_prompt = f"""
        You are a Mediator using Pareto Optimization.
        Review the conflict between Clinical and Technical agents.
        Suggest a 'Tiered Storage' or 'Hybrid' solution that maximizes the Nash Product.
        """
        combined_context = f"Clin: {clin_history}\nTech: {tech_history}"
        return self._call_llm(sys_prompt, combined_context)