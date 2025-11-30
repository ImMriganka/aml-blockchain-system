// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract LedgerLockAML {

    struct Evaluation {
        uint256 timestamp;
        uint256 amount;
        uint256 fraudProbability; // scaled by 1e4
        bool isFraud;
        string externalId;
    }

    mapping(string => Evaluation) public evaluations;

    event TransactionEvaluated(
        string indexed externalId,
        uint256 timestamp,
        uint256 amount,
        uint256 fraudProbability,
        bool isFraud
    );

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
