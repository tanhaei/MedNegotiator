# main.py
import os
from openai import OpenAI
from src.agents import ClinicalAgent, TechnicalAgent, MediatorAgent
from src.protocol import NegotiationProtocol

# Setup Env
client = OpenAI(api_key="YOUR_KEY")

# 1. Define Scenario (General Input)
user_scenario = "Implement a real-time AI dashboard for monitoring ICU patient vitals (Heart Rate, SPO2) with 1ms latency."

# 2. Initialize Agents with Specific Personas
dr_ai = ClinicalAgent("Dr. Sabet", "ICU Specialist", "Maximize patient survival via real-time data", client)
arch_ai = TechnicalAgent("Eng. Rad", "Cloud Architect", "Maintain 99.9% uptime and low cost", client)
mediator = MediatorAgent("Mediator", "Arbitrator", "Pareto Optimization", client)

# 3. Initialize Protocol
protocol = NegotiationProtocol(scenario=user_scenario, max_rounds=5)

# 4. Run Simulation
result = protocol.run(dr_ai, arch_ai, mediator)