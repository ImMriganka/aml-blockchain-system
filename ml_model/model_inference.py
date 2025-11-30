# ml_model/model_inference.py

import numpy as np
import pandas as pd
import joblib
import shap

class FraudModel:
    def __init__(self):
        self.model = joblib.load("fraud_model.pkl")
        self.feature_names = joblib.load("feature_names.pkl")

        # Initialize SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)

    def _prepare_input(self, transaction: dict) -> pd.DataFrame:
        df = pd.DataFrame([transaction])

        df = pd.get_dummies(df, columns=["sender_country", "receiver_country"])

        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0

        df = df[self.feature_names]
        return df

    def predict_proba(self, transaction: dict) -> float:
        df = self._prepare_input(transaction)

        prob = self.model.predict_proba(df)

        # Always convert to scalar
        if hasattr(prob, "__len__"):
            prob = prob[0][1]

        return float(prob)

    def explain(self, transaction: dict) -> dict:
        df = self._prepare_input(transaction)

        shap_values = self.explainer.shap_values(df)

        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        explanation = dict(zip(self.feature_names, shap_values[0]))

        top_features = dict(
            sorted(explanation.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        )

        return top_features


