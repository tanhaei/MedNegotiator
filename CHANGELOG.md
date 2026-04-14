# Change Log

## Key corrections against the original repository snapshot

1. **Configuration**
   - Removed the hard-coded placeholder API key from `main.py`.
   - Added `.env`-driven configuration and defaulted to `gpt-4o`.

2. **Dependencies**
   - Repaired `requirements.txt`, which was previously malformed and not installable.

3. **Protocol correctness**
   - Fixed the broken negotiation loop where `current_proposal` was never updated.
   - Added actual alternating offers, deadlock detection, and mediator fallback.

4. **Mathematical alignment with the paper**
   - Updated utility calculations to reflect the paper's `U_clin`, `U_tech`, and Nash product.
   - Added hard-constraint rejection instead of relying on a soft floor.

5. **Safety / consistency alignment**
   - Added a deterministic consistency guard with semantic anchoring and hard rule checks.

6. **Reproducibility**
   - Added deterministic offline behavior so the repository works even without a live LLM API key.
