"""
Legacy single-file implementation of the Ledger-Lock AML system.

The project has been refactored into a modular architecture with:
- `ml_model` for training and inference
- `aml` for KYC + rule-based checks + ML orchestration
- `blockchain` for local and on-chain persistence

For the full system, use `python main.py` instead of this file.
This module is kept only for reference and backward compatibility.
"""

"""
Legacy entrypoint kept for backwards compatibility.
Use `main.py` or the modular package for new functionality.
"""

from main import run_demo


if __name__ == "__main__":
    run_demo()

