const { expect }  = require("chai");
const { ethers }  = require("hardhat");

describe("TouristDID", function () {
  let contract, admin, tourist, police, hospital, stranger;
  const MOCK_CID   = "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco";
  const MOCK_HASH  = ethers.keccak256(ethers.toUtf8Bytes("test-document-content"));

  beforeEach(async () => {
    [admin, tourist, police, hospital, stranger] = await ethers.getSigners();
    const TouristDID = await ethers.getContractFactory("TouristDID");
    contract = await TouristDID.deploy();
    await contract.waitForDeployment();
  });

  describe("Deployment", () => {
    it("sets admin correctly", async () => {
      expect(await contract.admin()).to.equal(admin.address);
    });
  });

  describe("DID Registration", () => {
    it("registers a new DID", async () => {
      await expect(contract.connect(tourist).registerDID(MOCK_CID, MOCK_HASH))
        .to.emit(contract, "DIDRegistered")
        .withArgs(tourist.address, MOCK_CID, await latestTimestamp());
    });

    it("prevents double registration", async () => {
      await contract.connect(tourist).registerDID(MOCK_CID, MOCK_HASH);
      await expect(contract.connect(tourist).registerDID(MOCK_CID, MOCK_HASH))
        .to.be.revertedWith("TouristDID: DID already registered");
    });

    it("rejects empty CID", async () => {
      await expect(contract.connect(tourist).registerDID("", MOCK_HASH))
        .to.be.revertedWith("TouristDID: CID cannot be empty");
    });
  });

  describe("Emergency Access", () => {
    beforeEach(async () => {
      await contract.connect(tourist).registerDID(MOCK_CID, MOCK_HASH);
    });

    it("grants emergency access to police", async () => {
      await expect(contract.connect(tourist).grantEmergencyAccess(police.address))
        .to.emit(contract, "EmergencyAccessGranted")
        .withArgs(tourist.address, police.address);
      expect(await contract.hasAccess(tourist.address, police.address)).to.be.true;
    });

    it("allows pre-authorised police to fetch CID", async () => {
      await contract.connect(tourist).grantEmergencyAccess(police.address);
      const cid = await contract.connect(police).getIdentityCID(tourist.address);
      expect(cid).to.equal(MOCK_CID);
    });

    it("blocks stranger from accessing CID", async () => {
      await expect(contract.connect(stranger).getIdentityCID(tourist.address))
        .to.be.revertedWith("TouristDID: access denied");
    });

    it("revokes access correctly", async () => {
      await contract.connect(tourist).grantEmergencyAccess(police.address);
      await contract.connect(tourist).revokeEmergencyAccess(police.address);
      expect(await contract.hasAccess(tourist.address, police.address)).to.be.false;
    });
  });

  describe("SOS Mechanism", () => {
    beforeEach(async () => {
      await contract.connect(tourist).registerDID(MOCK_CID, MOCK_HASH);
      await contract.addAuthority(police.address);
    });

    it("authorised authority can activate SOS", async () => {
      await expect(contract.connect(police).activateSOS(tourist.address))
        .to.emit(contract, "SOSActivated");
    });

    it("SOS allows any authorised authority to access CID", async () => {
      await contract.connect(hospital).registerDID(MOCK_CID, MOCK_HASH); // just to have hospital
      await contract.addAuthority(hospital.address);
      await contract.connect(police).activateSOS(tourist.address);
      // hospital didn't have pre-auth, but SOS is active
      const cid = await contract.connect(hospital).getIdentityCID(tourist.address);
      expect(cid).to.equal(MOCK_CID);
    });

    it("tourist can deactivate SOS", async () => {
      await contract.connect(police).activateSOS(tourist.address);
      await contract.connect(tourist).deactivateSOS(tourist.address);
      const [,sosActive] = await contract.getPublicInfo(tourist.address);
      expect(sosActive).to.be.false;
    });
  });

  describe("Public Info", () => {
    it("returns public metadata without personal data", async () => {
      await contract.connect(tourist).registerDID(MOCK_CID, MOCK_HASH);
      const [exists, sosActive, dataHash] = await contract.getPublicInfo(tourist.address);
      expect(exists).to.be.true;
      expect(sosActive).to.be.false;
      expect(dataHash).to.equal(MOCK_HASH);
    });
  });

  async function latestTimestamp() {
    const block = await ethers.provider.getBlock("latest");
    return block.timestamp;
  }
});
