from web3 import Web3
import json
from pathlib import Path

# =========================
# HARDHAT CONFIG
# =========================

HARDHAT_RPC = "http://127.0.0.1:8545"

CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

ABI_PATH = Path(__file__).resolve().parent / "Lock.json"


class EthereumClient:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(HARDHAT_RPC))

        if not self.w3.is_connected():
            raise Exception("❌ Cannot connect to Hardhat blockchain")

        # Auto select first account from Hardhat
        self.account = self.w3.eth.accounts[0]

        # Load ABI
        if not ABI_PATH.exists():
            raise Exception(f"❌ ABI file not found at {ABI_PATH}")

        with open(ABI_PATH) as f:
            abi = json.load(f)

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=abi
        )

        print("✅ Connected to Ethereum")
        print("Account:", self.account)
        print("Contract:", CONTRACT_ADDRESS)

    def save_transaction(self, tx_hash: str, aml_status: str, fraud_score: float):
        """
        Stores transaction reference into Ethereum blockchain
        (like audit log, not actual money transfer)
        """

        try:
            tx = self.contract.functions.lock().transact({
                "from": self.account
            })

            receipt = self.w3.eth.wait_for_transaction_receipt(tx)

            print("✅ Stored on Ethereum")
            print("Block:", receipt.blockNumber)
            print("Hash:", receipt.transactionHash.hex())

            return {
                "block_number": receipt.blockNumber,
                "transaction_hash": receipt.transactionHash.hex(),
                "status": "stored_on_ethereum"
            }

        except Exception as e:
            print("❌ Ethereum write failed:", str(e))
            return {
                "status": "eth_error",
                "error": str(e)
            }


# For manual test
if __name__ == "__main__":
    eth = EthereumClient()
    result = eth.save_transaction(
        tx_hash="DEMO_TX_12345",
        aml_status="approved",
        fraud_score=0.12
    )
    print(result)
