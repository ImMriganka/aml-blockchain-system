
'''

import pandas as pd
import joblib
import hashlib
import time
import random

# Load Fraud Detection Model
fraud_model = joblib.load("fraud_model.pkl")

# Load Feature Names
feature_names = joblib.load("feature_names.pkl")

# Blockchain Class (For Secure Transaction Storage)
class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(previous_hash="0", data={"system": "Blockchain Initialized"})

    def create_block(self, previous_hash, data):
        block_content = f"{previous_hash}{data}{time.time()}"
        block_hash = hashlib.sha256(block_content.encode()).hexdigest()
        block = {"index": len(self.chain) + 1, "previous_hash": previous_hash, "data": data, "hash": block_hash}
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1] if self.chain else None

# Initialize Blockchain
blockchain = Blockchain()

# Risk Analysis Function (Before AI Prediction)
def assess_risk(transaction):
    risk_score = 0
    risk_factors = []

    if transaction["amount"] > 10000:
        risk_score += 2
        risk_factors.append("🔴 High Transaction Amount")

    if transaction["transaction_speed"] < 2:
        risk_score += 1
        risk_factors.append("🟠 Very Fast Transaction")

    if transaction["sender_country"] != transaction["receiver_country"]:
        risk_score += 1
        risk_factors.append("🟡 Cross-Border Transfer")

    return risk_score, risk_factors

# Process Transactions (Multiple Transactions Supported)
def process_transactions(transactions):
    results = []

    for tx in transactions:
        print("\n🔍 Processing Transaction:")
        print(tx)

        # Perform Risk Analysis
        risk_score, risk_factors = assess_risk(tx)
        print(f"📊 Risk Score: {risk_score} / 4")
        for factor in risk_factors:
            print(f"   - {factor}")

        # Convert Transaction to DataFrame
        df = pd.DataFrame([tx])

        # One-hot encoding (matching training features)
        df = pd.get_dummies(df, columns=["sender_country", "receiver_country"])

        # Ensure all expected columns exist (add missing ones with value 0)
        for col in feature_names:
            if col not in df.columns:
                df[col] = 0

        # Reorder columns to match training order
        df = df[feature_names]

        # AI Fraud Prediction
        fraud_probability = fraud_model.predict_proba(df)[0][1]  # Get probability
        is_fraud = fraud_probability > 0.5  # Threshold-based fraud detection

        # Blockchain Storage
        last_block = blockchain.get_last_block()
        blockchain.create_block(last_block["hash"], {"transaction": tx, "fraud_probability": round(fraud_probability * 100, 2)})

        # Display Results
        print(f"🤖 AI Fraud Probability: {round(fraud_probability * 100, 2)}%")
        print(f"🚨 Fraud Detected: {'✅ YES' if is_fraud else '❌ NO'}")

        results.append({"transaction": tx, "fraud_probability": round(fraud_probability * 100, 2), "is_fraud": is_fraud})

    return results
    


# Example Transactions
transactions_list = [
    {"amount": 5000, "sender_balance": 20000, "receiver_balance": 15000, "transaction_speed": 2, "sender_country": "IN", "receiver_country": "US"},
    {"amount": 15000, "sender_balance": 50000, "receiver_balance": 30000, "transaction_speed": 1, "sender_country": "UK", "receiver_country": "SG"},
    {"amount": 800, "sender_balance": 4000, "receiver_balance": 2000, "transaction_speed": 3, "sender_country": "IN", "receiver_country": "IN"},
    {"amount": 22000, "sender_balance": 60000, "receiver_balance": 10000, "transaction_speed": 1, "sender_country": "US", "receiver_country": "UK"}
]

# Start Processing
print("\n🚀 Starting Transaction Processing...")
processed_results = process_transactions(transactions_list)

'''

# transaction_fraud_checker.py
import json
from pathlib import Path
import pandas as pd
import joblib
import hashlib
import time
from typing import List, Dict, Any

# Paths (resolve relative to this file)
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "fraud_model.pkl"
FEATURES_PATH = BASE_DIR / "feature_names.pkl"
CHAIN_PATH = BASE_DIR / "chain_tf.json"


def _safe_load(path: Path, desc: str = "artifact"):
    try:
        return joblib.load(path)
    except Exception as exc:
        raise RuntimeError(f"Failed loading {desc} from {path}: {exc}")


# Load model + features (raises helpful error if missing)
fraud_model = _safe_load(MODEL_PATH, "fraud model")
feature_names = _safe_load(FEATURES_PATH, "feature names")


class Blockchain:
    """Simple persistent local blockchain for logging transactions."""

    def __init__(self, persist_file: Path = CHAIN_PATH) -> None:
        self.persist_file = persist_file
        self.chain: List[Dict[str, Any]] = []
        self._load_or_init()

    def _initial_block(self) -> Dict[str, Any]:
        ts = time.time()
        data = {"system": "blockchain_initialized", "timestamp": ts}
        h = self._hash_block(1, "0", ts, data)
        return {"index": 1, "previous_hash": "0", "timestamp": ts, "data": data, "hash": h}

    def _hash_block(self, index: int, previous_hash: str, timestamp: float, data: Any) -> str:
        payload = f"{index}{previous_hash}{timestamp}{json.dumps(data, sort_keys=True)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_or_init(self) -> None:
        if self.persist_file.exists():
            try:
                with open(self.persist_file, "r", encoding="utf-8") as f:
                    self.chain = json.load(f)
                # Basic validation: ensure chain isn't empty
                if not isinstance(self.chain, list) or len(self.chain) == 0:
                    self.chain = [self._initial_block()]
                    self._persist()
            except Exception:
                # If loading fails, start with a genesis block
                self.chain = [self._initial_block()]
                self._persist()
        else:
            self.chain = [self._initial_block()]
            self._persist()

    def _persist(self) -> None:
        try:
            with open(self.persist_file, "w", encoding="utf-8") as f:
                json.dump(self.chain, f, indent=2, sort_keys=True)
        except Exception:
            # In production, log the exception
            pass

    def get_last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    def create_block(self, previous_hash: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new block. `data` should be a sanitized dict (no raw PII).
        We also inject a timestamp into both block top-level and data for compatibility.
        """
        prev = self.get_last_block()
        index = prev["index"] + 1
        timestamp = time.time()

        # Ensure data contains timestamp
        data_copy = dict(data)
        data_copy.setdefault("timestamp", timestamp)

        block_hash = self._hash_block(index, previous_hash, timestamp, data_copy)
        block = {
            "index": index,
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "data": data_copy,
            "hash": block_hash,
        }
        self.chain.append(block)
        self._persist()
        return block

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(reversed(self.chain[-limit:]))


# Create global blockchain used by this script
blockchain = Blockchain()


def assess_risk(tx: Dict[str, Any]) -> tuple[int, list[str]]:
    """Rule-based heuristic before AI prediction."""
    risk_score = 0
    factors: list[str] = []

    try:
        amount = float(tx.get("amount", 0.0))
    except Exception:
        amount = 0.0

    if amount > 10000:
        risk_score += 2
        factors.append("High Amount")

    try:
        speed = int(tx.get("transaction_speed", 3))
    except Exception:
        speed = 3

    if speed < 2:
        risk_score += 1
        factors.append("Very Fast Transaction")

    if tx.get("sender_country") != tx.get("receiver_country"):
        risk_score += 1
        factors.append("Cross-Border")

    return risk_score, factors


def _prepare_features(tx: Dict[str, Any]) -> pd.DataFrame:
    # Build a single-row DataFrame and one-hot encode the country fields (same approach as training)
    df = pd.DataFrame([tx])
    df = pd.get_dummies(df, columns=["sender_country", "receiver_country"])
    # Ensure all expected columns exist
    for col in feature_names:
        if col not in df.columns:
            df[col] = 0
    df = df[feature_names]
    return df


def process_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of transactions, run risk heuristics + ML, write sanitized blocks.
    Returns a list of result dicts.
    """
    results: List[Dict[str, Any]] = []

    for idx, tx in enumerate(transactions, start=1):
        external_id = tx.get("external_id") or f"cli-tx-{int(time.time())}-{idx}"
        print("\n🔍 Processing:", external_id)

        risk_score, risk_factors = assess_risk(tx)
        print(f"📊 Risk Score: {risk_score} ({', '.join(risk_factors) or 'none'})")

        df = _prepare_features(tx)

        # predict_proba may raise; guard it
        try:
            # model.predict_proba expects a 2D array/DataFrame — we pass df
            prob = float(fraud_model.predict_proba(df)[0][1])
        except Exception:
            prob = 0.0

        # clamp to [0,1]
        prob = max(0.0, min(1.0, prob))
        is_fraud = prob >= 0.5

        # Build sanitized payload for block (no raw PII)
        block_payload = {
            "external_id": external_id,
            "status": "flagged_fraud" if is_fraud else "approved",
            "fraud_probability": prob,
        }

        block = blockchain.create_block(blockchain.get_last_block()["hash"], block_payload)

        print(f"🤖 Fraud Probability: {round(prob * 100, 2)}%")
        print(f"🚨 Fraud Detected: {'YES' if is_fraud else 'NO'}")
        print(f"🔗 Block #{block['index']} created: {block['hash'][:12]}...")

        results.append({
            "external_id": external_id,
            "transaction": tx,
            "fraud_probability": prob,
            "is_fraud": is_fraud,
            "block_index": block["index"],
            "block_hash": block["hash"],
        })

    return results


if __name__ == "__main__":
    # Quick example/demo run
    sample_transactions = [
        {"amount": 5000, "sender_balance": 20000, "receiver_balance": 15000, "transaction_speed": 2,
         "sender_country": "IN", "receiver_country": "US", "sender_id": "IN12345", "receiver_id": "US67890"},
        {"amount": 30000, "sender_balance": 50000, "receiver_balance": 25000, "transaction_speed": 1,
         "sender_country": "UK", "receiver_country": "SG", "sender_id": "UK54321", "receiver_id": "SG34567"},
    ]

    out = process_transactions(sample_transactions)
    print("\nProcessed results:")
    print(json.dumps(out, indent=2))
