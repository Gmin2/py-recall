from json import loads
from pathlib import Path
from typing import Any

from .exceptions import UnexpectedError


def read_abi_file_to_json(path: Path) -> dict[Any, Any]:
    """Read an ABI file and parse it as JSON."""
    with open(path) as f:
        data = loads(f.read())
        return data["abi"] if isinstance(data, dict) and "abi" in data else {}


# Subnet IDs
TESTNET_SUBNET_ID = "/r314159/t410frrql2ooeoz2t4hlor3hqw33druwnc4jzhajdbeq"
LOCALNET_SUBNET_ID = "/r31337/t410f6gbdxrbehnaeeo4mrq7wc5hgq6smnefys4qanwi"
DEVNET_SUBNET_ID = "test"

# Chain IDs
TESTNET_PARENT_CHAIN_ID = 314159
TESTNET_CHAIN_ID = 2481632
LOCALNET_PARENT_CHAIN_ID = 31337
LOCALNET_CHAIN_ID = 248163216
DEVNET_CHAIN_ID = 1942764459484029

# CometBFT RPC URLs
TESTNET_RPC_URL = "https://api.testnet.recall.chain.love"
LOCALNET_RPC_URL = "http://127.0.0.1:26657"
DEVNET_RPC_URL = "http://127.0.0.1:26657"

# EVM RPC URLs
TESTNET_EVM_RPC_URL = "https://evm.testnet.recall.chain.love"
TESTNET_EVM_WS_URL = "wss://evm.testnet.recall.chain.love"
TESTNET_PARENT_EVM_RPC_URL = "https://api.calibration.node.glif.io/rpc/v1"
LOCALNET_EVM_RPC_URL = "http://127.0.0.1:8645"
LOCALNET_EVM_WS_URL = "ws://127.0.0.1:8645"
LOCALNET_PARENT_EVM_RPC_URL = "http://127.0.0.1:8545"
DEVNET_EVM_RPC_URL = "http://127.0.0.1:8545"
DEVNET_EVM_WS_URL = "ws://127.0.0.1:8545"

# Objects API URLs
TESTNET_OBJECT_API_URL = "https://objects.testnet.recall.chain.love"
LOCALNET_OBJECT_API_URL = "http://127.0.0.1:8001"
DEVNET_OBJECT_API_URL = "http://127.0.0.1:8001"

# Gateway manager addresses
TESTNET_PARENT_EVM_GATEWAY_ADDRESS = "0x136066500b332e7D72643EE7690E9C708702c7e6"
TESTNET_EVM_GATEWAY_ADDRESS = "0x77aa40b105843728088c0132e43fc44348881da8"
LOCALNET_PARENT_EVM_GATEWAY_ADDRESS = "0x9A676e781A523b5d0C0e43731313A708CB607508"
LOCALNET_EVM_GATEWAY_ADDRESS = "0x77aa40b105843728088c0132e43fc44348881da8"
DEVNET_EVM_GATEWAY_ADDRESS = "0x77aa40b105843728088c0132e43fc44348881da8"

# Subnet registry addresses
TESTNET_PARENT_EVM_REGISTRY_ADDRESS = "0xdf3Fe12002826Ff617F2d7500c61B72A8e3E9436"
TESTNET_EVM_REGISTRY_ADDRESS = "0x74539671a1d2f1c8f200826baba665179f53a1b7"
LOCALNET_PARENT_EVM_REGISTRY_ADDRESS = "0x322813Fd9A801c5507c9de605d63CEA4f2CE6c44"
LOCALNET_EVM_REGISTRY_ADDRESS = "0x74539671a1d2f1c8f200826baba665179f53a1b7"
DEVNET_EVM_REGISTRY_ADDRESS = "0x74539671a1d2f1c8f200826baba665179f53a1b7"

# Supply source (ERC20) addresses
TESTNET_EVM_SUPPLY_SOURCE_ADDRESS = "0x9E5ea73a639484CcE57F865dC1E582Cd01F3251F"
LOCALNET_EVM_SUPPLY_SOURCE_ADDRESS = "0x4A679253410272dd5232B3Ff7cF5dbB88f295319"

# Contract ABIs
IMACHINE_FACADE_ABI = read_abi_file_to_json(Path(__file__).parent / "abis" / "IMachineFacade.json")
BUCKET_MANAGER_ABI = read_abi_file_to_json(Path(__file__).parent / "abis" / "BucketManager.json")
BLOB_MANAGER_ABI = read_abi_file_to_json(Path(__file__).parent / "abis" / "BlobManager.json")
CREDIT_MANAGER_ABI = read_abi_file_to_json(Path(__file__).parent / "abis" / "CreditManager.json")
GATEWAY_MANAGER_FACET_ABI = read_abi_file_to_json(Path(__file__).parent / "abis" / "GatewayManagerFacet.json")
IERC20_ABI = read_abi_file_to_json(Path(__file__).parent / "abis" / "IERC20.json")

# Wrapper contract addresses, and addresses above formatted in the same way
BLOB_MANAGER_ADDRESS = {
    2481632: "0x27594F8412bA08278b15b55C6347605Ee3b2020C",  # testnet -- TODO: update this upon new testnet deployments
    248163216: "0x8ce361602B935680E8DeC218b820ff5056BeB7af",  # localnet
}

BUCKET_MANAGER_ADDRESS = {
    2481632: "0x170a22c76a2Bb7c5F1b0e7067a0ddb7C3452c8e0",  # testnet -- TODO: update this upon new testnet deployments
    248163216: "0xeD1DB453C3156Ff3155a97AD217b3087D5Dc5f6E",  # localnet
}

CREDIT_MANAGER_ADDRESS = {
    2481632: "0x296042865b783D8E8Fb09F04FFAE2A66a16B85Bc",  # testnet -- TODO: update this upon new testnet deployments
    248163216: "0x196dBCBb54b8ec4958c959D8949EBFE87aC2Aaaf",  # localnet
}

GATEWAY_MANAGER_FACET_ADDRESS = {
    314159: TESTNET_PARENT_EVM_GATEWAY_ADDRESS,  # calibration
    2481632: TESTNET_EVM_GATEWAY_ADDRESS,  # testnet
    31337: LOCALNET_PARENT_EVM_GATEWAY_ADDRESS,  # anvil
    248163216: LOCALNET_EVM_GATEWAY_ADDRESS,  # localnet
    1942764459484029: DEVNET_EVM_GATEWAY_ADDRESS,  # devnet
}

SUPPLY_SOURCE_ADDRESS = {
    314159: TESTNET_EVM_SUPPLY_SOURCE_ADDRESS,  # calibration (for testnet)
    31337: LOCALNET_EVM_SUPPLY_SOURCE_ADDRESS,  # anvil (for localnet)
}

# Miscellaneous
RPC_TIMEOUT = 60_000
MIN_TTL = 3600  # one hour
MAX_OBJECT_LENGTH = 5_000_000_000  # 5GB


def get_evm_rpc_url(chain_id: int) -> str:
    """Get the EVM RPC URL for a given chain ID."""
    if chain_id == 314159:  # calibration
        return TESTNET_PARENT_EVM_RPC_URL
    elif chain_id == 2481632:  # testnet
        return TESTNET_EVM_RPC_URL
    elif chain_id == 31337:  # anvil
        return LOCALNET_PARENT_EVM_RPC_URL
    elif chain_id == 248163216:  # localnet
        return LOCALNET_EVM_RPC_URL
    elif chain_id == 1942764459484029:  # devnet
        return DEVNET_EVM_RPC_URL
    else:
        raise UnexpectedError(UnexpectedError.UNKNOWN_CHAIN_ID.format(chain_id))


def get_object_api_url(chain_id: int) -> str:
    """Get the object API URL for a given chain ID."""
    if chain_id == 2481632:  # testnet
        return TESTNET_OBJECT_API_URL
    elif chain_id == 248163216:  # localnet
        return LOCALNET_OBJECT_API_URL
    elif chain_id == 1942764459484029:  # devnet
        return DEVNET_OBJECT_API_URL
    else:
        raise UnexpectedError(UnexpectedError.UNKNOWN_CHAIN_ID.format(chain_id))
