const hre = require("hardhat");

async function main() {
  const LedgerLockAML = await hre.ethers.getContractFactory("LedgerLockAML");

  const contract = await LedgerLockAML.deploy();

  await contract.waitForDeployment();

  const address = await contract.getAddress();

  console.log("✅ LedgerLockAML deployed to:", address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
;

