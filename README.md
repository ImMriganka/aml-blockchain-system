# 🚀 LedgerLock – AI & Blockchain AML System

> **A hybrid Anti-Money Laundering (AML) detection system combining Machine Learning transparency with Blockchain immutability.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)
![Solidity](https://img.shields.io/badge/Solidity-0.8.0-363636)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📖 Overview

**LedgerLock** is an open-source framework designed to solve the "black box" problem in financial fraud detection. It uses **Machine Learning** to predict fraud probability and a **Custom Local Blockchain** (anchored to Ethereum) to create a tamper-proof audit trail of those predictions.

This system ensures that once a transaction is flagged and recorded, the data cannot be altered, providing a verifiable history for auditors.

---

## ✨ Key Features

### ✅ 1. AI-Powered Fraud Detection
Utilizes a **Scikit-learn** model to analyze transaction metadata in real-time.
* Calculates Fraud Probability & AML Risk Level.
* Automated KYC checks and compliance rule verification.

### ✅ 2. Custom Local Blockchain (The Audit Layer)
Every evaluated transaction is sealed into a block containing:
* **Merkle Root:** For efficient data verification.
* **RSA Digital Signatures:** Ensures block authenticity.
* **Timestamp & Previous Hash:** Enforces chronological chain integrity.

### ✅ 3. Ethereum Smart Contract Integration
Critical data is anchored to the Ethereum network via `LedgerLockAML.sol`.
* Stores: External ID, Amount, and Fraud Flag permanently.
* Powered by **Hardhat** local development environment.

### ✅ 4. Real-Time Dashboard
A **Flask** web interface providing:
* Live visualization of the blockchain.
* Risk Heatmaps and Transaction Simulators.
* Links to Ethereum Tx Hashes.

---

## 🛠️ Tech Stack

| Component | Technologies |
| :--- | :--- |
| **Backend** | Python, Flask |
| **Machine Learning** | Scikit-learn, Pandas, NumPy |
| **Blockchain (Local)** | Python (Custom Chain), RSA Encryption, Merkle Trees |
| **Blockchain (Public)** | Solidity, Hardhat, Web3.py |
| **Frontend** | HTML5, CSS3, Chart.js (Dashboard) |

---

## 📂 Project Structure

```text
ledgerlock/
│
├── aml/                 # AML pipeline & Business Logic
│   └── pipeline.py
│
├── blockchain/          # Custom Python Blockchain Implementation
│   ├── local_chain.py
│   └── contracts_LedgerLockAML.sol
│
├── ml_model/            # Machine Learning Inference
│   └── model_inference.py
│
├── eth/                 # Hardhat (Ethereum) Environment
│   ├── contracts/
│   ├── scripts/
│   └── hardhat.config.js
│
├── templates/           # Flask UI Templates
│   └── index.html
│
├── static/              # Assets (JS, CSS, Images)
├── app.py               # Main Flask Application
├── requirements.txt     # Python Dependencies
└── README.md



## 🚀 Installation & Setup

### 1\. Clone the Repository

```bash
git clone [https://github.com/ImMriganka/ledgerlock-aml-system.git](https://github.com/ImMriganka/ledgerlock-aml-system.git)
cd ledgerlock-aml-system
```

### 2\. Install Python Dependencies

It is recommended to use a virtual environment.

```bash
pip install -r requirements.txt
```

### 3\. Start the Local Ethereum Node (Hardhat)

Open a new terminal window:

```bash
cd eth
npx hardhat node
```

### 4\. Deploy Smart Contract

In a separate terminal (keep the node running):

```bash
cd eth
npx hardhat run scripts/deploy.js --network localhost
```

*Note the contract address output and update your `app.py` config if necessary.*

### 5\. Run the Application

```bash
# Return to the root directory
cd ..
python app.py
```

**Access the Dashboard:** 👉 `http://127.0.0.1:5000`

-----

## 📦 API Routes

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Home Dashboard & Stats |
| `POST` | `/` | Submit a Manual Transaction for Analysis |
| `GET` | `/api/chain` | Retrieve recent blocks from the local chain |
| `GET` | `/api/risk-map` | Get data for the Risk Heatmap visualization |

-----

## 🔐 Security Architecture

  * **RSA Signatures:** Each block is signed by a private RSA key and verified using a public key to prevent identity spoofing.
  * **Immutable Storage:** `storeEvaluation` function in Solidity ensures that once an AML score is written to Ethereum, it cannot be deleted.

-----

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for full details.

## 🙌 Author

**Mriganka Bairagi**

  * Open Source Software Project – AML + Blockchain System
  * GitHub: [@ImMriganka](https://www.google.com/search?q=https://github.com/ImMriganka)

