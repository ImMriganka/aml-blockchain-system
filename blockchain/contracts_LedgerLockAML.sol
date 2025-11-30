SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title LedgerLockAML
 * @dev Minimal smart contract to record AML evaluation results on-chain.
 *
 * In a real deployment this would live in a separate Solidity project
 * (Hardhat/Foundry/Truffle). Here we provide the contract code so you can
 * compile and deploy it to a testnet or local Ethereum node.
 */
contract LedgerLockAML {
    struct Evaluation {
        uint256 timestamp;
        uint256 amount;
        uint256 fraudProbability; // scaled by 1e4 (e.g., 0.7534 -> 7534)
        bool isFraud;
        string externalId; // off-chain reference (e.g., transaction hash / UUID)
    }

    event TransactionEvaluated(
        string indexed externalId,
        uint256 timestamp,
        uint256 amount,
        uint256 fraudProbability,
        bool isFraud
    );

    mapping(string => Evaluation) public evaluations;

    function storeEvaluation(
        string calldata externalId,
        uint256 amount,
        uint256 fraudProbability,
        bool isFraud
    ) external {
        Evaluation memory e = Evaluation({
            timestamp: block.timestamp,
            amount: amount,
            fraudProbability: fraudProbability,
            isFraud: isFraud,
            externalId: externalId
        });

        evaluations[externalId] = e;

        emit TransactionEvaluated(
            externalId,
            e.timestamp,
            amount,
            fraudProbability,
            isFraud
        );
    }
}


