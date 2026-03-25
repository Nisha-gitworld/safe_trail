// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * SafeTrail — Tourist Digital Identity Contract
 * ───────────────────────────────────────────────
 * Deployed on Polygon (Mumbai testnet for dev, PoS mainnet for prod).
 *
 * Design:
 *  • Raw personal data is NEVER stored on-chain.
 *  • Only an IPFS CID (pointer to encrypted document) is stored.
 *  • Emergency access is pre-authorised by the tourist during onboarding.
 *  • ZK-proof integration hooks are included for future selective disclosure.
 */

contract TouristDID {

    // ── Structs ──────────────────────────────────────────────────────────────
    struct Identity {
        string  ipfsCID;        // Points to AES-256 encrypted doc on IPFS
        bytes32 dataHash;       // SHA-256 of raw document (integrity verification)
        address owner;
        bool    exists;
        bool    sosActive;      // True during an active emergency
        uint256 registeredAt;
        uint256 lastUpdated;
    }

    // ── State ─────────────────────────────────────────────────────────────────
    mapping(address => Identity)              private identities;
    mapping(address => mapping(address => bool)) private emergencyAccess;
    mapping(address => bool)                  public  authorisedAuthorities;
    address public                            admin;

    // ── Events ────────────────────────────────────────────────────────────────
    event DIDRegistered(address indexed tourist, string cid, uint256 timestamp);
    event DIDUpdated(address indexed tourist, string newCid, uint256 timestamp);
    event EmergencyAccessGranted(address indexed tourist, address indexed authority);
    event EmergencyAccessRevoked(address indexed tourist, address indexed authority);
    event SOSActivated(address indexed tourist, uint256 timestamp);
    event SOSDeactivated(address indexed tourist, uint256 timestamp);
    event AuthorityAdded(address indexed authority);
    event AuthorityRemoved(address indexed authority);

    // ── Modifiers ─────────────────────────────────────────────────────────────
    modifier onlyAdmin() {
        require(msg.sender == admin, "TouristDID: caller is not admin");
        _;
    }

    modifier onlyOwner(address tourist) {
        require(
            msg.sender == identities[tourist].owner,
            "TouristDID: caller is not the identity owner"
        );
        _;
    }

    modifier identityExists(address tourist) {
        require(identities[tourist].exists, "TouristDID: identity not registered");
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────────────
    constructor() {
        admin = msg.sender;
    }

    // ── Admin Functions ───────────────────────────────────────────────────────
    function addAuthority(address _authority) external onlyAdmin {
        authorisedAuthorities[_authority] = true;
        emit AuthorityAdded(_authority);
    }

    function removeAuthority(address _authority) external onlyAdmin {
        authorisedAuthorities[_authority] = false;
        emit AuthorityRemoved(_authority);
    }

    // ── Tourist Functions ─────────────────────────────────────────────────────
    /**
     * @dev Register a new DID. Can only be called once per address.
     * @param _ipfsCID  IPFS content ID of the encrypted identity document
     * @param _dataHash SHA-256 hash of the raw document for integrity checks
     */
    function registerDID(string calldata _ipfsCID, bytes32 _dataHash) external {
        require(!identities[msg.sender].exists, "TouristDID: DID already registered");
        require(bytes(_ipfsCID).length > 0, "TouristDID: CID cannot be empty");

        Identity storage id = identities[msg.sender];
        id.ipfsCID       = _ipfsCID;
        id.dataHash      = _dataHash;
        id.owner         = msg.sender;
        id.exists        = true;
        id.sosActive     = false;
        id.registeredAt  = block.timestamp;
        id.lastUpdated   = block.timestamp;

        emit DIDRegistered(msg.sender, _ipfsCID, block.timestamp);
    }

    /**
     * @dev Update IPFS CID (e.g. when tourist renews passport).
     */
    function updateDID(string calldata _newCID, bytes32 _newDataHash)
        external
        identityExists(msg.sender)
        onlyOwner(msg.sender)
    {
        identities[msg.sender].ipfsCID     = _newCID;
        identities[msg.sender].dataHash    = _newDataHash;
        identities[msg.sender].lastUpdated = block.timestamp;
        emit DIDUpdated(msg.sender, _newCID, block.timestamp);
    }

    /**
     * @dev Pre-authorise an emergency authority (police wallet, hospital wallet).
     *      Called during tourist onboarding.
     */
    function grantEmergencyAccess(address _authority)
        external
        identityExists(msg.sender)
        onlyOwner(msg.sender)
    {
        emergencyAccess[msg.sender][_authority] = true;
        emit EmergencyAccessGranted(msg.sender, _authority);
    }

    /**
     * @dev Revoke emergency access.
     */
    function revokeEmergencyAccess(address _authority)
        external
        identityExists(msg.sender)
        onlyOwner(msg.sender)
    {
        emergencyAccess[msg.sender][_authority] = false;
        emit EmergencyAccessRevoked(msg.sender, _authority);
    }

    /**
     * @dev Activate SOS — called by the backend service when SOS is triggered.
     *      Requires caller to be the tourist or an authorised authority.
     */
    function activateSOS(address _tourist)
        external
        identityExists(_tourist)
    {
        require(
            msg.sender == _tourist || authorisedAuthorities[msg.sender],
            "TouristDID: not authorised to activate SOS"
        );
        identities[_tourist].sosActive = true;
        emit SOSActivated(_tourist, block.timestamp);
    }

    function deactivateSOS(address _tourist)
        external
        identityExists(_tourist)
        onlyOwner(_tourist)
    {
        identities[_tourist].sosActive = false;
        emit SOSDeactivated(_tourist, block.timestamp);
    }

    // ── View Functions ────────────────────────────────────────────────────────
    /**
     * @dev Fetch IPFS CID — only callable by:
     *      1. The tourist themselves, OR
     *      2. A pre-authorised authority, OR
     *      3. Any authorised authority while SOS is active
     */
    function getIdentityCID(address _tourist)
        external
        view
        identityExists(_tourist)
        returns (string memory)
    {
        bool isOwner      = msg.sender == _tourist;
        bool isPreAuth    = emergencyAccess[_tourist][msg.sender];
        bool isSOSAuthority = identities[_tourist].sosActive &&
                              authorisedAuthorities[msg.sender];

        require(isOwner || isPreAuth || isSOSAuthority, "TouristDID: access denied");
        return identities[_tourist].ipfsCID;
    }

    /**
     * @dev Returns public metadata (no personal data).
     */
    function getPublicInfo(address _tourist)
        external
        view
        identityExists(_tourist)
        returns (
            bool   exists,
            bool   sosActive,
            bytes32 dataHash,
            uint256 registeredAt,
            uint256 lastUpdated
        )
    {
        Identity storage id = identities[_tourist];
        return (id.exists, id.sosActive, id.dataHash, id.registeredAt, id.lastUpdated);
    }

    function hasAccess(address _tourist, address _authority)
        external
        view
        returns (bool)
    {
        return emergencyAccess[_tourist][_authority];
    }
}
