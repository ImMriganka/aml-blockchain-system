
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Set
from urllib.parse import urlparse

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization


class LocalBlockchain:
    """
    Local blockchain with:
    - chain.json persistence
    - Merkle-root based hashing
    - Proof-of-Work OR Proof-of-Authority style blocks
    - RSA digital signatures per block
    - Basic multi-node support (node registry + chain replacement)
    - Simple wallet/balance computation based on sender_id / receiver_id
    """

    CHAIN_FILE = "chain.json"
    DEFAULT_DIFFICULTY = 4  # used when in PoW mode

    def __init__(self, consensus: str = "poa", difficulty: int | None = None) -> None:
        """
        consensus: "pow" or "poa"
        - "pow": mine blocks with Proof of Work (leading-zero hash, nonce, difficulty)
        - "poa": Proof of Authority style (no mining loop, authority-signed blocks)
        """
        if consensus not in {"pow", "poa"}:
            raise ValueError("consensus must be 'pow' or 'poa'")

        self.consensus: str = consensus
        self.chain: List[Dict[str, Any]] = []
        self.nodes: Set[str] = set()  # peers like "127.0.0.1:5001"
        self.difficulty: int = difficulty if difficulty is not None else self.DEFAULT_DIFFICULTY

        # Each node has its own key pair (identity / authority)
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self._public_key = self._private_key.public_key()

        # Load chain from disk if present
        self.load_chain()

        if not self.chain:
            # No chain on disk → fresh genesis
            print("ℹ️ No chain.json found – creating fresh genesis chain")
            self._init_fresh_chain()
        else:
            # Validate loaded chain; if invalid, reset
            if not LocalBlockchain.is_valid_chain(self.chain):
                print("⚠️ Stored chain.json is invalid – resetting to fresh genesis")
                self._init_fresh_chain()
            else:
                print(f"ℹ️ Loaded valid chain from disk (length={len(self.chain)})")

    # ------------------------------------------------------------------
    # Internal helper to create a fresh chain (genesis only)
    # ------------------------------------------------------------------
    def _init_fresh_chain(self) -> None:
        self.chain = []
        self.create_genesis_block()
        self.save_chain()

    # ------------------------------------------------------------------
    # Genesis block
    # ------------------------------------------------------------------
    def create_genesis_block(self) -> None:
        genesis_data = {"system": "Blockchain Initialized"}
        self.create_block(genesis_data)

    # ------------------------------------------------------------------
    # Merkle root
    # ------------------------------------------------------------------
    def calculate_merkle_root(self, data: Dict[str, Any]) -> str:
        """
        Simple Merkle root for a single transaction dict:
        SHA256(sorted(JSON(data)))
        """
        serialized = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(serialized).hexdigest()

    @staticmethod
    def _calculate_merkle_for_block(block: Dict[str, Any]) -> str:
        data = block.get("data", {}) or {}
        serialized = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(serialized).hexdigest()

    # ------------------------------------------------------------------
    # Hash helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_pow_hash(previous_hash: str, timestamp: int, merkle_root: str, nonce: int) -> str:
        payload = f"{previous_hash}{timestamp}{merkle_root}{nonce}".encode()
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _compute_poa_hash(previous_hash: str, timestamp: int, merkle_root: str, authority_id: str) -> str:
        payload = f"{previous_hash}{timestamp}{merkle_root}{authority_id}".encode()
        return hashlib.sha256(payload).hexdigest()

    def _authority_id(self) -> str:
        """
        Return a compact identifier for this authority node based on its public key.
        """
        public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        digest = hashlib.sha256(public_pem.encode()).hexdigest()
        # Shorten for readability
        return digest[:16]

    # ------------------------------------------------------------------
    # Digital signature helpers
    # ------------------------------------------------------------------
    def _sign_data(self, data: Dict[str, Any]) -> bytes:
        """
        Sign the JSON-serialized data dict with this node's private key.
        """
        data_str = json.dumps(data, sort_keys=True)
        signature = self._private_key.sign(
            data_str.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return signature

    @staticmethod
    def _verify_signature(public_pem: str, data: Dict[str, Any], signature_hex: str) -> bool:
        """
        Verify an RSA-PSS signature for the given data dict using the supplied public key.
        """
        try:
            public_key = serialization.load_pem_public_key(public_pem.encode())
            data_str = json.dumps(data, sort_keys=True)
            signature = bytes.fromhex(signature_hex)

            public_key.verify(
                signature,
                data_str.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Block creation (PoW or PoA) + Signature
    # ------------------------------------------------------------------
    def create_block(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new block:
        - If consensus == "pow": mine with Proof-of-Work (nonce, difficulty, leading zeros)
        - If consensus == "poa": Proof-of-Authority style (no mining loop, authority_id in hash)
        - Always sign the data with this node's RSA private key.
        """
        timestamp = int(time.time())
        previous_hash = self.chain[-1]["hash"] if self.chain else "0"
        merkle_root = self.calculate_merkle_root(data)

        if self.consensus == "pow":
            nonce = 0
            difficulty = self.difficulty
            prefix = "0" * difficulty

            # Proof-of-Work loop
            while True:
                block_hash = self._compute_pow_hash(previous_hash, timestamp, merkle_root, nonce)
                if block_hash.startswith(prefix):
                    break
                nonce += 1

            authority_id = None  # not used in PoW mode

        else:  # Proof of Authority
            difficulty = 0
            nonce = 0
            authority_id = self._authority_id()
            block_hash = self._compute_poa_hash(previous_hash, timestamp, merkle_root, authority_id)

        # Sign the data payload
        signature_bytes = self._sign_data(data)
        signature_hex = signature_bytes.hex()

        public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        block: Dict[str, Any] = {
            "index": len(self.chain) + 1,
            "timestamp": timestamp,
            "data": data,
            "merkle_root": merkle_root,
            "previous_hash": previous_hash,
            "hash": block_hash,
            "nonce": nonce,
            "difficulty": difficulty,
            "consensus": self.consensus,
            "signature": signature_hex,
            "public_key": public_pem,
        }

        if authority_id is not None:
            block["authority_id"] = authority_id

        self.chain.append(block)
        self.save_chain()
        return block

    # ------------------------------------------------------------------
    # Public sink interface used by AMLPipeline
    # ------------------------------------------------------------------
    def store_evaluation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        AMLPipeline calls sink.store_evaluation(result).
        We mine/create a new block containing that evaluation.
        """
        return self.create_block(evaluation)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def is_chain_valid(self) -> bool:
        """Validate the current local chain."""
        return self.is_valid_chain(self.chain)

    @staticmethod
    def is_valid_chain(chain: List[Dict[str, Any]]) -> bool:
        """
        Validate a provided chain (used for multi-node consensus).
        Checks:
        - previous_hash links
        - Merkle root matches data
        - hash matches either PoW or PoA formula
        - if difficulty > 0 → PoW leading zeros
        - RSA signature is valid for each block's data
        """
        if not chain:
            return False

        for i in range(len(chain)):
            block = chain[i]

            # 0) Basic required fields
            for field in ("timestamp", "data", "merkle_root", "hash"):
                if field not in block:
                    print(f"❌ Block {i} missing field '{field}'")
                    return False

            # 1) previous_hash must match (except for genesis)
            if i > 0:
                previous = chain[i - 1]
                if block.get("previous_hash") != previous.get("hash"):
                    print(f"❌ Invalid previous hash at block {i}")
                    return False

            # 2) Merkle root must match data
            recalculated_merkle = LocalBlockchain._calculate_merkle_for_block(block)
            if block.get("merkle_root") != recalculated_merkle:
                print(f"❌ Invalid merkle root at block {i}")
                return False

            # 3) Hash & consensus checks
            try:
                timestamp = int(block.get("timestamp", 0))
                prev_hash = block.get("previous_hash", "")
                merkle_root = block.get("merkle_root", "")
                nonce = int(block.get("nonce", 0)) if "nonce" in block else 0
                difficulty = int(block.get("difficulty", 0)) if "difficulty" in block else 0
            except Exception:
                print(f"❌ Invalid numeric fields at block {i}")
                return False

            consensus = block.get("consensus", "pow" if difficulty > 0 else "poa")

            if consensus == "pow":
                recomputed_hash = LocalBlockchain._compute_pow_hash(prev_hash, timestamp, merkle_root, nonce)
                if recomputed_hash != block.get("hash"):
                    print(f"❌ Invalid PoW block hash at block {i}")
                    return False

                if difficulty > 0 and not recomputed_hash.startswith("0" * difficulty):
                    print(f"❌ PoW block {i} does not satisfy difficulty={difficulty}")
                    return False

            else:  # "poa"
                authority_id = block.get("authority_id", "")
                recomputed_hash = LocalBlockchain._compute_poa_hash(prev_hash, timestamp, merkle_root, authority_id)
                if recomputed_hash != block.get("hash"):
                    print(f"❌ Invalid PoA block hash at block {i}")
                    return False

            # 4) RSA signature validation (skip genesis if it has no signature)
            signature_hex = block.get("signature")
            public_pem = block.get("public_key")
            if signature_hex and public_pem:
                ok = LocalBlockchain._verify_signature(
                    public_pem,
                    block.get("data", {}) or {},
                    signature_hex,
                )
                if not ok:
                    print(f"❌ Invalid signature at block {i}")
                    return False

        return True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_chain(self) -> None:
        with open(self.CHAIN_FILE, "w") as file:
            json.dump(self.chain, file, indent=4)

    def load_chain(self) -> None:
        path = Path(self.CHAIN_FILE)
        if path.exists():
            try:
                with open(self.CHAIN_FILE, "r") as file:
                    self.chain = json.load(file)
            except Exception as e:
                print(f"⚠️ Failed to load existing chain.json ({e}) – starting fresh")
                self.chain = []

    # ------------------------------------------------------------------
    # Multi-node helpers
    # ------------------------------------------------------------------
    def register_node(self, address: str) -> None:
        """
        Register a peer node.
        Accepts forms like:
          - "http://127.0.0.1:5001"
          - "127.0.0.1:5001"
        Internally we store only "host:port".
        """
        parsed = urlparse(address)
        netloc = parsed.netloc or parsed.path  # handle both with/without scheme
        if netloc:
            self.nodes.add(netloc)

    def replace_chain(self, new_chain: List[Dict[str, Any]]) -> bool:
        """
        Replace local chain with a longer, valid chain from peers.
        Returns True if replaced, False otherwise.
        """
        if not new_chain:
            return False

        if len(new_chain) <= len(self.chain):
            return False

        if not LocalBlockchain.is_valid_chain(new_chain):
            return False

        self.chain = new_chain
        self.save_chain()
        return True

    # ------------------------------------------------------------------
    # Convenience / Wallet-like balance computation
    # ------------------------------------------------------------------
    def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return most recent N blocks (for UI charts etc.)."""
        return self.chain[-limit:]

    def compute_balances(self) -> Dict[str, float]:
        """
        Compute balances for each logical 'wallet' based on sender_id / receiver_id
        in the AML evaluation data stored in blocks.

        We treat:
          - data["transaction"]["sender_id"] as the debit wallet
          - data["transaction"]["receiver_id"] as the credit wallet
          - data["transaction"]["amount"] as the transferred amount

        This lets you show a wallet-style view even though the project
        started as AML transaction logs.
        """
        balances: Dict[str, float] = {}

        for block in self.chain:
            data = block.get("data", {}) or {}
            tx = data.get("transaction", {}) or {}

            if not tx:
                continue  # skip genesis or non-tx blocks

            sender = tx.get("sender_id")
            receiver = tx.get("receiver_id")

            try:
                amount = float(tx.get("amount", 0) or 0)
            except Exception:
                amount = 0.0

            if sender:
                balances[sender] = balances.get(sender, 0.0) - amount
            if receiver:
                balances[receiver] = balances.get(receiver, 0.0) + amount

        return balances

    def get_balance(self, wallet_id: str) -> float:
        """Return the computed balance for a given sender_id / receiver_id."""
        return self.compute_balances().get(wallet_id, 0.0)
