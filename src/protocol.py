from termcolor import colored
from src.engine import QFDEngine

class NegotiationSession:
    def __init__(self, clinical_agent, technical_agent, mediator_agent):
        self.clin = clinical_agent
        self.tech = technical_agent
        self.med = mediator_agent
        self.rounds = 0
        self.max_rounds = 5
        self.history = []

    def run(self):
        print(colored("--- Starting MedNegotiator Simulation: WSI Storage Conflict ---", "cyan", attrs=['bold']))
        
        # Initial Proposal
        self.rounds = 1
        proposal = self.clin.simulate_response(1, "")
        self.log_turn(self.clin, proposal)
        
        # Evaluation
        u_clin = QFDEngine.calculate_clinical_utility(proposal)
        u_tech = QFDEngine.calculate_technical_utility(proposal)
        self.log_stats(u_clin, u_tech)

        if u_tech < 0.4:
            print(colored(f"[System] Technical Agent rejects proposal (U_tech {u_tech} < Threshold)", "red"))
            
            # Counter Proposal
            counter = self.tech.simulate_response(1, proposal)
            self.log_turn(self.tech, counter)
            
            # Round 2
            self.rounds = 2
            defense = self.clin.simulate_response(2, counter) # Simulation logic
            # (Skipping full logic for brevity of the demo file)
            
            # Round 3 - Mediation Trigger
            self.rounds = 3
            print(colored("\n[System] Deadlock Detected! Triggering Mediator...", "yellow"))
            
            solution = self.med.propose_solution()
            self.log_turn(self.med, solution)
            
            # Final Agreement
            response_clin = self.clin.simulate_response(3, solution)
            response_tech = self.tech.simulate_response(3, solution)
            
            self.log_turn(self.clin, response_clin)
            self.log_turn(self.tech, response_tech)
            
            # Final Stats
            u_clin_final = 0.85
            u_tech_final = 0.78
            nash = QFDEngine.calculate_nash_product(u_clin_final, u_tech_final)
            self.log_stats(u_clin_final, u_tech_final, nash)
            print(colored(f"\n[Result] Consensus Reached. Nash Product: {nash:.2f}", "green", attrs=['bold']))

    def log_turn(self, agent, message):
        print(f"\n[{agent.role}] {agent.name}: {message}")
        self.history.append(f"{agent.name}: {message}")

    def log_stats(self, uc, ut, nash=None):
        msg = f"   >>> Metrics: U_clin={uc:.2f}, U_tech={ut:.2f}"
        if nash:
            msg += f", Nash={nash:.2f}"
        print(colored(msg, "grey"))
