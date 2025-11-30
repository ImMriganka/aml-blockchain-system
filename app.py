
from datetime import datetime, timezone
from typing import Any, Dict
import random
import threading
import time

from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    flash,
    redirect,
    url_for,
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)

from web3 import Web3

from aml.pipeline import AMLPipeline
from blockchain.local_chain import LocalBlockchain
from ml_model.model_inference import FraudModel


# -----------------------------------------------------------------------------
# ETHEREUM (Hardhat) SETUP
# -----------------------------------------------------------------------------

HARDHAT_RPC = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = Web3.to_checksum_address("0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9")

CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "externalId", "type": "string"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "fraudProbability", "type": "uint256"},
            {"internalType": "bool", "name": "isFraud", "type": "bool"}
        ],
        "name": "storeEvaluation",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

w3 = Web3(Web3.HTTPProvider(HARDHAT_RPC))

if w3.is_connected():
    print("\n✅ Connected to Hardhat Network")
    DEFAULT_ACCOUNT = w3.eth.accounts[0]
    CONTRACT = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
else:
    print("\n❌ Hardhat not running on :8545")
    CONTRACT = None
    DEFAULT_ACCOUNT = None


# -----------------------------------------------------------------------------
# Flask app
# -----------------------------------------------------------------------------

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.secret_key = "replace-with-secure-random-string"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# -----------------------------------------------------------------------------
# USERS
# -----------------------------------------------------------------------------

USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "analyst": {"password": "analyst123", "role": "analyst"},
    "auditor": {"password": "auditor123", "role": "auditor"},
}


class User(UserMixin):
    def __init__(self, username: str, role: str) -> None:
        self.id = username
        self.role = role


@login_manager.user_loader
def load_user(user_id: str):
    data = USERS.get(user_id)
    if not data:
        return None
    return User(user_id, data["role"])


# -----------------------------------------------------------------------------
# SYSTEM INITIALIZATION
# -----------------------------------------------------------------------------

fraud_model = FraudModel()
local_chain = LocalBlockchain()
pipeline = AMLPipeline(model=fraud_model, sink=local_chain)

print("Blockchain valid:", local_chain.is_chain_valid())
print("Current blocks:", len(local_chain.chain))


# -----------------------------------------------------------------------------
# ETHEREUM WRITE FUNCTION
# -----------------------------------------------------------------------------

def write_to_ethereum(external_id: str, amount: float, fraud_probability: float, status: str):
    if not CONTRACT:
        print("❌ CONTRACT not available")
        return None

    try:
        scaled_risk = int(float(fraud_probability) * 10000)
        is_fraud = True if status == "flagged_fraud" else False

        print(f"""
--- ETH WRITE ---
ID: {external_id}
Amount: {amount}
Risk: {scaled_risk}
Fraud: {is_fraud}
-----------------
""")

        tx = CONTRACT.functions.storeEvaluation(
            str(external_id),
            int(amount),
            scaled_risk,
            is_fraud
        ).transact({"from": DEFAULT_ACCOUNT})

        receipt = w3.eth.wait_for_transaction_receipt(tx)

        return {
            "eth_tx_hash": tx.hex(),
            "eth_block_number": receipt.blockNumber,
            "contract": CONTRACT_ADDRESS
        }

    except Exception as e:
        print("❌ Ethereum error:", str(e))
        return None


# -----------------------------------------------------------------------------
# AUTO TRANSACTION
# -----------------------------------------------------------------------------

AUTO_ENABLED = False
COUNTRIES = ["IN", "US", "UK", "SG", "NG", "RU"]


def generate_random_transaction():
    return {
        "amount": random.randint(100, 200000),
        "sender_balance": random.randint(2000, 100000),
        "receiver_balance": random.randint(2000, 100000),
        "transaction_speed": random.randint(1, 5),
        "sender_country": random.choice(COUNTRIES),
        "receiver_country": random.choice(COUNTRIES),
        "sender_id": "AUTO" + str(random.randint(1000, 9999)),
        "receiver_id": "AUTO" + str(random.randint(1000, 9999))
    }


def auto_simulator():
    global AUTO_ENABLED

    while True:
        if AUTO_ENABLED:
            try:
                tx_data = generate_random_transaction()
                external_id = f"AUTO-{int(time.time())}"

                evaluation = pipeline.evaluate_transaction(
                    tx_data,
                    external_id=external_id
                )

                fraud_prob = float(evaluation.get("fraud_probability", 0.0))
                status = evaluation.get("status", "review")

                eth = write_to_ethereum(
                    external_id,
                    tx_data["amount"],
                    fraud_prob,
                    status
                )

                if eth and len(local_chain.chain) > 0:
                    last_block = local_chain.chain[-1]

                    last_block["data"]["eth_tx_hash"] = eth["eth_tx_hash"]
                    last_block["data"]["eth_block_number"] = eth["eth_block_number"]

                    last_block["eth_tx_hash"] = eth["eth_tx_hash"]
                    last_block["eth_block_number"] = eth["eth_block_number"]

                    if "transaction" in last_block["data"]:
                        last_block["data"]["transaction"]["eth_tx_hash"] = eth["eth_tx_hash"]
                        last_block["data"]["transaction"]["eth_block_number"] = eth["eth_block_number"]

                    local_chain.save_chain()

                    print("\n✅ ETH SAVED TO BLOCK SUCCESSFULLY")
                    print("TX:", eth["eth_tx_hash"])
                    print("BLOCK:", eth["eth_block_number"])

            except Exception as e:
                print("Auto simulation error:", str(e))

        time.sleep(5)


threading.Thread(target=auto_simulator, daemon=True).start()


# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

def _parse_form(form) -> Dict[str, Any]:
    try:
        amount = float(form.get("amount", 0) or 0)
        sender_balance = float(form.get("sender_balance", 0) or 0)
        receiver_balance = float(form.get("receiver_balance", 0) or 0)
        tx_speed = int(form.get("transaction_speed", 2) or 2)
    except Exception:
        amount = sender_balance = receiver_balance = 0
        tx_speed = 2

    return {
        "amount": amount,
        "sender_balance": sender_balance,
        "receiver_balance": receiver_balance,
        "transaction_speed": tx_speed,
        "sender_country": form.get("sender_country") or "IN",
        "receiver_country": form.get("receiver_country") or "US",
        "sender_id": form.get("sender_id") or "IN12345",
        "receiver_id": form.get("receiver_id") or "US67890",
    }


# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    global AUTO_ENABLED

    result = None
    form_data = {}

    if request.method == "POST" and "toggle_auto" in request.form:
        AUTO_ENABLED = not AUTO_ENABLED
        flash("Auto Transaction Toggled", "success")
        return redirect(url_for("index"))

    if request.method == "POST" and "amount" in request.form:
        form_data = _parse_form(request.form)

        try:
            external_id = f"MANUAL-{int(time.time())}"

            evaluation = pipeline.evaluate_transaction(
                form_data,
                external_id=external_id
            )

            fraud_prob = float(evaluation.get("fraud_probability", 0.0))
            status = evaluation.get("status", "review")

            eth = write_to_ethereum(
                external_id,
                form_data["amount"],
                fraud_prob,
                status
            )

            if eth and len(local_chain.chain) > 0:
                last_block = local_chain.chain[-1]

                last_block["data"]["eth_tx_hash"] = eth["eth_tx_hash"]
                last_block["data"]["eth_block_number"] = eth["eth_block_number"]

                last_block["eth_tx_hash"] = eth["eth_tx_hash"]
                last_block["eth_block_number"] = eth["eth_block_number"]

                if "transaction" in last_block["data"]:
                    last_block["data"]["transaction"]["eth_tx_hash"] = eth["eth_tx_hash"]
                    last_block["data"]["transaction"]["eth_block_number"] = eth["eth_block_number"]

                local_chain.save_chain()

                print("\n✅ ETH SAVED TO BLOCK SUCCESSFULLY")
                print("TX:", eth["eth_tx_hash"])
                print("BLOCK:", eth["eth_block_number"])

            evaluation["fraud_probability"] = fraud_prob
            evaluation["ethereum"] = eth
            result = evaluation

            flash("✅ Stored on Local + Ethereum Blockchain", "success")

        except Exception as exc:
            flash(f"Error: {exc}", "danger")

    recent_blocks = local_chain.recent(limit=200)

    return render_template(
        "index.html",
        result=result,
        form=form_data,
        recent_blocks=recent_blocks,
        auto_enabled=AUTO_ENABLED,
        current_user=current_user,
    )


@app.route("/api/chain", methods=["GET"])
@login_required
def api_chain():
    return jsonify(local_chain.recent(limit=200))


@app.route("/api/risk-map", methods=["GET"])
@login_required
def risk_map():
    stats = {}

    for block in local_chain.chain:
        data = block.get("data", {}) or {}
        tx = data.get("transaction")

        if not tx:
            continue

        country = tx.get("receiver_country", "UNK")
        risk = float(data.get("fraud_probability", 0.0))

        if country not in stats:
            stats[country] = {"total": 0, "count": 0}

        stats[country]["total"] += risk
        stats[country]["count"] += 1

    result = [
        {"country": c, "avg_risk": round(v["total"] / v["count"], 4)}
        for c, v in stats.items()
        if v["count"] > 0
    ]

    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, port=5000)

