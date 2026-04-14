# MedNegotiator

This repository is a corrected, runnable reference implementation aligned more closely with the paper's architecture.

## What was fixed

- Replaced the broken dependency file with a valid `requirements.txt`.
- Removed the hard-coded API key pattern and switched to `.env` / environment-based configuration.
- Updated the default model name to `gpt-4o`, matching the paper.
- Implemented a normalized axiological engine with:
  - clinical utility `U_clin = w * phi - lambda * Psi`
  - technical utility normalized from budget, cost, and risk
  - Nash product calculation
  - hard-constraint rejection
- Added a lightweight `ConsistencyGuard` with:
  - semantic anchoring
  - predicate extraction
  - hard safety / budget checks
- Reworked the negotiation protocol into an actual alternating-offers process with:
  - round logs
  - deadlock detection
  - mediator fallback
- Added deterministic fallback logic so the demo runs even without an API key.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI key to `.env` only if you want live LLM calls. Without a key, the project runs in deterministic offline-demo mode.

## Usage

```bash
python main.py
```

Or pass a custom scenario:

```bash
python main.py --scenario "Store raw WSI files for research while keeping pathology review responsive."
```

## Files

- `src/agents.py`: persona-driven agents and deterministic fallbacks
- `src/engine.py`: utility calculations and Nash bargaining
- `src/guard.py`: consistency guard and semantic anchoring proxy
- `src/protocol.py`: negotiation rounds, deadlock detection, mediation
- `src/utils.py`: helpers for parsing and lightweight text similarity

## Notes

This is still a compact reference implementation, not the full research stack. The paper mentions FAISS-backed RAG, averaged multi-run scoring, and richer NL-to-FOL parsing. Those are represented here with lightweight placeholders so the code remains reproducible and self-contained.
