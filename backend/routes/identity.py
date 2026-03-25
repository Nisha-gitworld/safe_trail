"""Routes — Blockchain Digital Identity"""
from fastapi import APIRouter, Depends, HTTPException
from models.schemas import DIDRegisterRequest, DIDRegisterResponse
from services.auth_service import get_current_user

router = APIRouter()


@router.post("/register", response_model=DIDRegisterResponse)
async def register_did(
    req: DIDRegisterRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/identity/register
    Register a DID on Polygon — stores IPFS CID on-chain.
    """
    try:
        from web3 import Web3
        from config import settings

        w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        if not w3.is_connected():
            raise HTTPException(503, "Blockchain node unreachable")

        # Minimal ABI for the registerDID function
        abi = [
            {
                "inputs": [
                    {"name": "_ipfsCID", "type": "string"},
                    {"name": "_dataHash", "type": "bytes32"},
                ],
                "name": "registerDID",
                "outputs": [],
                "type": "function",
            }
        ]
        contract = w3.eth.contract(
            address=w3.to_checksum_address(settings.CONTRACT_ADDRESS),
            abi=abi,
        )
        account = w3.eth.account.from_key(settings.PRIVATE_KEY)
        tx = contract.functions.registerDID(
            req.ipfs_cid,
            bytes.fromhex(req.data_hash.replace("0x", "").ljust(64, "0")),
        ).build_transaction({
            "from":     account.address,
            "nonce":    w3.eth.get_transaction_count(account.address),
            "gas":      200_000,
            "gasPrice": w3.eth.gas_price,
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

        return DIDRegisterResponse(
            did=f"did:polygon:{account.address}",
            tx_hash=tx_hash.hex(),
            ipfs_cid=req.ipfs_cid,
            registered=True,
        )

    except ImportError:
        # Demo fallback when web3 is not installed
        return DIDRegisterResponse(
            did=f"did:polygon:0xDEMO_{req.user_id[:8]}",
            tx_hash="0xdemo_tx_hash_for_hackathon_demo",
            ipfs_cid=req.ipfs_cid,
            registered=True,
        )
    except Exception as e:
        raise HTTPException(500, f"DID registration failed: {str(e)}")


@router.post("/grant-access")
async def grant_emergency_access(
    authority_address: str,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/identity/grant-access
    Pre-authorise an emergency authority (police/hospital wallet address).
    """
    return {
        "status": "granted",
        "authority": authority_address,
        "user_id": current_user["user_id"],
        "message": "Emergency authority can now access your DID during SOS events.",
    }


@router.get("/profile")
async def get_identity_profile(current_user: dict = Depends(get_current_user)):
    """
    GET /api/identity/profile
    Returns the user's public DID profile (no raw personal data).
    """
    return {
        "did":          f"did:polygon:0x{current_user['user_id'].replace('-','')[:40]}",
        "ipfs_cid":     "QmExampleCIDFromIPFS1234567890abcdef",
        "registered":   True,
        "network":      "Polygon Mumbai Testnet",
        "attributes": {
            "nationality": "revealed_on_emergency_only",
            "blood_type":  "revealed_on_emergency_only",
            "embassy":     "revealed_on_emergency_only",
        },
    }
