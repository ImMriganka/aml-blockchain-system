📌 AML-FraudShield – Anti-Money Laundering System Using Blockchain & Machine Learning
🚀 End-to-End AML Transaction Monitoring System

Tech Stack: Python · Flask · Machine Learning · Pandas · Scikit-learn · Blockchain · Chart.js · HTML/CSS

✨ Overview

AML-FraudShield is a full-stack AML (Anti-Money Laundering) prototype that detects suspicious financial transactions using:

✔ Machine Learning fraud scoring

✔ Rule-based transaction analysis

✔ KYC identity validation

✔ Blockchain-based immutable audit logs

✔ Interactive web UI with charts and history explorer

This project demonstrates how modern AML pipelines work inside banks, FinTech platforms, cross-border payment systems, and compliance engines.

🧠 Features
🔍 1. Fraud Detection Pipeline

ML model predicts fraud probability (0–1 scale).

Custom rules identify:

unusual amounts

balance inconsistencies

velocity (transaction speed) anomalies

risky cross-border routes

🪪 2. KYC Validation

Checks sender/receiver identities.

Flags invalid or mismatched KYC IDs.

🔗 3. Blockchain Ledger

Every transaction evaluation is stored as a blockchain block:

index

timestamp

transaction data

ML score

rule-based decision

SHA-256 hash

previous hash

This ensures tamper-proof auditability.

📊 4. Web UI Dashboard

Clean dark UI

Fraud probability line chart

Transaction evaluation console

Paginated blockchain explorer

CSV download of the audit chain

Filters: search by ID, status, pagination

🧱 Architecture
User → Web UI → Flask Backend → AML Pipeline → ML Model
                                          ↘ Blockchain Ledger

📦 Project Structure
/aml
   ├── pipeline.py
/blockchain
   ├── local_chain.py
/ml_model
   ├── model_inference.py
/templates
   ├── index.html
   ├── explorer.html
app.py

▶️ How to Run
1. Install dependencies
pip install -r requirements.txt

2. Start the app
python app.py

3. Open UI
http://127.0.0.1:5000

📁 CSV Audit Export

Download all blockchain records via:

/download_audit

🧪 API Example
GET /api/chain?limit=30


Returns recent blockchain blocks in JSON.

📌 Future Enhancements

Real-time streaming ingestion

Graph-based entity link analysis

Advanced ML models (XGBoost, DNN)

Risk dashboards for compliance officers

📝 License

MIT