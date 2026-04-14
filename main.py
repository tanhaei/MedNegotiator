from __future__ import annotations

import argparse
import json
import os
from typing import Optional

from dotenv import load_dotenv

from src.agents import ClinicalAgent, MediatorAgent, TechnicalAgent
from src.protocol import NegotiationProtocol


def build_openai_client() -> Optional[object]:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except Exception:
        return None
    return OpenAI(api_key=api_key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MedNegotiator demo.")
    parser.add_argument(
        "--scenario",
        default=os.getenv(
            "NEGOTIATION_SCENARIO",
            "Implement a real-time AI dashboard for monitoring ICU patient vitals (Heart Rate, SpO2) with 1ms latency.",
        ),
        help="Scenario to negotiate.",
    )
    parser.add_argument("--max-rounds", type=int, default=6, help="Maximum negotiation rounds.")
    args = parser.parse_args()

    client = build_openai_client()

    dr_ai = ClinicalAgent(
        name="Dr. Sabet",
        role="ICU Specialist",
        goal="Maximize patient survival via safe and timely clinical visibility",
        client=client,
    )
    arch_ai = TechnicalAgent(
        name="Eng. Rad",
        role="Cloud Architect",
        goal="Maintain feasible latency, manageable cost, and reliable operations",
        client=client,
    )
    mediator = MediatorAgent(
        name="Mediator",
        role="Arbitrator",
        goal="Maximize the safety-feasible Nash product",
        client=client,
    )

    protocol = NegotiationProtocol(scenario=args.scenario, max_rounds=args.max_rounds)
    result = protocol.run(dr_ai, arch_ai, mediator)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
