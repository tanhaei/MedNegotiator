from src.agents import ClinicalAgent, TechnicalAgent, MediatorAgent
from src.protocol import NegotiationSession
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize Agents
    dr_ai = ClinicalAgent()
    arch_ai = TechnicalAgent()
    mediator = MediatorAgent()
    
    # Initialize Protocol
    session = NegotiationSession(dr_ai, arch_ai, mediator)
    
    # Run Simulation
    session.run()

if __name__ == "__main__":
    main()
