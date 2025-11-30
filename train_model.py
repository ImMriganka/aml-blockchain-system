"""
Legacy training entry point.

This file now delegates to ml_model.train_model so that all training
logic lives in the ml_model package.
"""

from ml_model.train_model import train_fraud_model


if __name__ == "__main__":
    train_fraud_model()
