"""
Main entry point for the Ledger-Lock AML system.

This script wires together:
- The trained fraud detection model
- The AML evaluation pipeline (KYC + rules + ML)
- The local blockchain as an immutable audit log

Optionally, you can extend this to also push results to an
on-chain smart contract using `blockchain.eth_client.EthereumAMLClient`.
"""

from typing import List, Dict, Any

from aml.pipeline import AMLPipeline
from blockchain.local_chain import LocalBlockchain
from ml_model.model_inference import FraudModel


def demo_transactions() -> List[Dict[str, Any]]:
    return [
        {
            "amount": 5000,
            "sender_balance": 20000,
            "receiver_balance": 15000,
            "transaction_speed": 2,
            "sender_country": "IN",
            "receiver_country": "US",
            "sender_id": "IN12345",
            "receiver_id": "US67890",
        },
        {
            "amount": 30000,
            "sender_balance": 50000,
            "receiver_balance": 25000,
            "transaction_speed": 1,
            "sender_country": "UK",
            "receiver_country": "SG",
            "sender_id": "UK54321",
            "receiver_id": "SG34567",
        },
        {
            "amount": 12000,
            "sender_balance": 30000,
            "receiver_balance": 15000,
            "transaction_speed": 3,
            "sender_country": "IN",
            "receiver_country": "IN",
            "sender_id": "IN12345",
            "receiver_id": "IN12345",
        },
        {
            "amount": 26000,
            "sender_balance": 70000,
            "receiver_balance": 20000,
            "transaction_speed": 1,
            "sender_country": "US",
            "receiver_country": "UK",
            "sender_id": "US67890",
            "receiver_id": "UK54321",
        },
    ]


def run_demo() -> None:
    model = FraudModel()
    local_chain = LocalBlockchain()
    pipeline = AMLPipeline(model=model, sink=local_chain)

    print("\n🚀 Starting Ledger-Lock AML System (modular architecture)...\n")

    for idx, tx in enumerate(demo_transactions(), start=1):
        external_id = f"tx-{idx}"
        print(f"\n🔍 Processing {external_id}: {tx}")
        result = pipeline.evaluate_transaction(tx, external_id=external_id)

        fraud_pct = round(result.get("fraud_probability", 0.0) * 100, 2) if "fraud_probability" in result else None
        if fraud_pct is not None:
            print(f"🤖 AI Fraud Probability: {fraud_pct}%")
        print(f"📌 Status: {result['status']} (reason: {result.get('reason', result.get('rule_reason', 'OK'))})")

    print("\n📚 Final local blockchain state (audit log) contains "
          f"{len(local_chain.chain)} blocks.\n")


if __name__ == "__main__":
    run_demo()


