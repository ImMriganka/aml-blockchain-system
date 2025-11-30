

# ml_model/train_model.py

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
from pathlib import Path
import json
from datetime import datetime, timezone

BLACKLISTED_COUNTRIES = {"NG", "IR", "KP", "RU"}
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "transactions.csv"
MODEL_PATH = BASE_DIR / "fraud_model.pkl"
FEATURES_PATH = BASE_DIR / "feature_names.pkl"
METADATA_PATH = BASE_DIR / "model_metadata.json"


def train_fraud_model(
    data_path: Path = DATA_PATH,
    model_path: Path = MODEL_PATH,
    features_path: Path = FEATURES_PATH,
    metadata_path: Path = METADATA_PATH,
) -> None:
    """Train RandomForest model & persist feature names and metadata."""
    df = pd.read_csv(data_path)
    
    # =============================
    #  FEATURE ENGINEERING
    # =============================

    # 1. Transactions per sender (velocity proxy)
    df["tx_per_hour"] = df.groupby(["sender_country", "sender_balance"])["amount"].transform("count")


    # 2. Average transaction amount per sender
    df["avg_tx_amount"] = df.groupby(["sender_country", "sender_balance"])["amount"].transform("mean")


    # 3. Z-score: how unusual transaction is
    df["z_score"] = (df["amount"] - df["avg_tx_amount"]) / (df["amount"].std() + 1e-9)

    # 4. Blacklisted country flag
    df["is_blacklisted_country"] = df["receiver_country"].apply(
    lambda x: 1 if x in BLACKLISTED_COUNTRIES else 0
    )

    # 5. Account age (mocked realistic bank data)
    df["account_age_days"] = np.random.randint(30, 3650, size=len(df))


    # Minimal checks
    if "is_fraud" not in df.columns:
        raise ValueError("Dataset missing required `is_fraud` column")

    # One-hot encode categorical features (training-time approach)
    df_enc = pd.get_dummies(df, columns=["sender_country", "receiver_country"])

    X = df_enc.drop(columns=["is_fraud"])
    y = df_enc["is_fraud"]

    feature_names = X.columns.tolist()
    joblib.dump(feature_names, features_path)

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)

    joblib.dump(model, model_path)

    meta = {
        
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_path": str(model_path),
        "features_path": str(features_path),
        "n_features": len(feature_names),
        "n_samples": int(len(df)),
        "model_type": "RandomForestClassifier",
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"✅ Model saved to {model_path}")
    print(f"✅ Feature list saved to {features_path}")
    print(f"✅ Metadata saved to {metadata_path}")


if __name__ == "__main__":
    train_fraud_model()
