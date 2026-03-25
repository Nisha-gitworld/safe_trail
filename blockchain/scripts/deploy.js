const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying TouristDID with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "MATIC");

  const TouristDID = await ethers.getContractFactory("TouristDID");
  const contract   = await TouristDID.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("\n✅ TouristDID deployed to:", address);
  console.log("   Network:", hre.network.name);
  console.log("\n📋 Add to your .env:");
  console.log(`   CONTRACT_ADDRESS=${address}`);

  // Add a default emergency authority (mock police wallet for demo)
  const MOCK_POLICE_WALLET = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8";
  const tx = await contract.addAuthority(MOCK_POLICE_WALLET);
  await tx.wait();
  console.log("\n🚔 Mock police authority added:", MOCK_POLICE_WALLET);

  // Save deployment info
  const fs = require("fs");
  const info = {
    network:    hre.network.name,
    address:    address,
    deployer:   deployer.address,
    deployedAt: new Date().toISOString(),
  };
  fs.writeFileSync("deployment.json", JSON.stringify(info, null, 2));
  console.log("\n💾 Deployment info saved to deployment.json");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
