
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol, Tuple

from ml_model.model_inference import FraudModel


class EvaluationSink(Protocol):
    def store_evaluation(self, evaluation: Dict[str, Any]) -> Any:
        ...


@dataclass
class AMLConfig:
    high_value_threshold: float = 25_000.0
    fraud_threshold: float = 0.5


class AMLPipeline:
    def __init__(
        self,
        model: FraudModel,
        sink: EvaluationSink,
        config: AMLConfig | None = None,
    ) -> None:
        self.model = model
        self.sink = sink
        self.config = config or AMLConfig()

        self.verified_users = {"IN12345", "US67890", "SG34567"}

    def check_kyc(self, transaction: Dict[str, Any]) -> bool:
        sender = transaction.get("sender_id")
        receiver = transaction.get("receiver_id")
        return sender in self.verified_users and receiver in self.verified_users

    def enforce_rules(self, transaction: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            amount = float(transaction.get("amount", 0.0))
        except (TypeError, ValueError):
            return False, "Invalid amount value"

        if amount > self.config.high_value_threshold:
            return False, "High-risk transaction amount"

        return True, "Compliant"

    def evaluate_transaction(self, transaction: Dict[str, Any], external_id: str) -> Dict[str, Any]:

        result: Dict[str, Any] = {
            "external_id": external_id,
            "transaction": transaction,
        }

        # Step 1: KYC
        kyc_ok = self.check_kyc(transaction)
        result["kyc_ok"] = kyc_ok

        if not kyc_ok:
            result.update({
                "status": "rejected_kyc",
                "reason": "KYC verification failed",
            })
            self.sink.store_evaluation(result)
            return result

        # Step 2: RULE CHECKS
        compliant, reason = self.enforce_rules(transaction)
        result["rule_compliant"] = compliant
        result["rule_reason"] = reason

        if not compliant:
            result.update({
                "status": "rejected_rules",
                "reason": reason,
            })
            self.sink.store_evaluation(result)
            return result

        # Step 3: ML FRAUD PREDICTION
        fraud_prob = self.model.predict_proba(transaction)

        # ✅ Force scalar float to avoid numpy truth errors
        try:
            fraud_prob = float(fraud_prob)
        except Exception:
            fraud_prob = float(fraud_prob[0])

        is_fraud = fraud_prob >= self.config.fraud_threshold

        result["fraud_probability"] = fraud_prob
        result["is_fraud"] = bool(is_fraud)
        result["status"] = "flagged_fraud" if is_fraud else "approved"

        # Step 4: XAI explanation
        try:
            explanation = self.model.explain(transaction)
            result["explanation"] = explanation
        except Exception as e:
            result["explanation"] = {"error": str(e)}

        self.sink.store_evaluation(result)
        return result
