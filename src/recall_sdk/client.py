"""
Recall client and wrapper contract interactions
"""

from typing import Any, TypeVar, cast, Dict, Optional

import requests
from eth_account.account import LocalAccount
from eth_typing import ChecksumAddress
from eth_utils import currency, to_checksum_address
from web3 import Account, Web3
from web3._utils.events import EventLogErrorFlags
from web3.contract import Contract
from web3.exceptions import ContractLogicError
from web3.types import HexBytes, Nonce, TxReceipt

from .constants import (
    BLOB_MANAGER_ABI,
    BLOB_MANAGER_ADDRESS,
    BUCKET_MANAGER_ABI,
    BUCKET_MANAGER_ADDRESS,
    CREDIT_MANAGER_ABI,
    CREDIT_MANAGER_ADDRESS,
    IMACHINE_FACADE_ABI,
    RPC_TIMEOUT,
    TESTNET_CHAIN_ID,
    LOCALNET_CHAIN_ID,
    DEVNET_CHAIN_ID,
    TESTNET_SUBNET_ID,
    get_evm_rpc_url,
    get_object_api_url,
)
from .exceptions import ContractError, ObjectNotFoundError, UnexpectedError
from .types import CreatedBucketResponse, EventLog
from .entities.ipc.subnet import SubnetId
from .entities.account import AccountManager
from .entities.blob import BlobManager
from .entities.bucket import BucketManager
from .entities.credit import CreditManager 

T = TypeVar("T")

ContractConfig = Dict[int, ChecksumAddress]


class ContractOverrides:
    """Contract address overrides configuration"""
    
    def __init__(
        self,
        bucket_manager: Optional[ContractConfig] = None,
        blob_manager: Optional[ContractConfig] = None,
        credit_manager: Optional[ContractConfig] = None,
        account_manager: Optional[Dict[str, ContractConfig]] = None,
    ):
        self.bucket_manager = bucket_manager or {}
        self.blob_manager = blob_manager or {}
        self.credit_manager = credit_manager or {}
        self.account_manager = account_manager or {
            "gateway_manager": {},
            "recall_erc20": {},
        }

class Client:
    """
    Recall client and wrapper contract interactions
    """

    w3: Web3
    signer: Optional[LocalAccount]
    evm_rpc_url: str
    object_api_url: str
    chain_id: int
    contract_overrides: ContractOverrides
    subnet_id: SubnetId

    def __init__(
        self,
        private_key: Optional[str] = None,
        chain_id: int = TESTNET_CHAIN_ID,
        evm_rpc_url: Optional[str] = None,
        object_api_url: Optional[str] = None,
        contract_overrides: Optional[ContractOverrides] = None,
    ):
        # Set up web3 instance, signer, and objects API
        if evm_rpc_url is None:
            evm_rpc_url = get_evm_rpc_url(chain_id)
        if object_api_url is None:
            object_api_url = get_object_api_url(chain_id)
        w3 = Web3(Web3.HTTPProvider(evm_rpc_url))
        self.w3 = w3
        self.signer = Account.from_key(private_key)
        self.object_api_url = object_api_url
        self.chain_id = chain_id
        self.contract_overrides = contract_overrides or ContractOverrides()

        # Set up signer if private key provided
        if private_key:
            self.signer = Account.from_key(private_key)
        else:
            self.signer = None

        # Initialize subnet ID
        if chain_id == TESTNET_CHAIN_ID:
            self.subnet_id = SubnetId.from_string(TESTNET_SUBNET_ID)
        else:
            # TODO: Add support for other chains
            self.subnet_id = SubnetId.from_chain(chain_id)
            
        # Set up Recall contracts
        # chain_id = self.get_chain_id()
        # blob_manager_addr = BLOB_MANAGER_ADDRESS[chain_id]
        # bucket_manager_addr = BUCKET_MANAGER_ADDRESS[chain_id]
        # credit_manager_addr = CREDIT_MANAGER_ADDRESS[chain_id]
        # self.blob_manager = self.w3.eth.contract(address=to_checksum_address(blob_manager_addr), abi=BLOB_MANAGER_ABI)
        # self.bucket_manager = self.w3.eth.contract(
        #     address=to_checksum_address(bucket_manager_addr), abi=BUCKET_MANAGER_ABI
        # )
        # self.credit_manager = self.w3.eth.contract(
        #     address=to_checksum_address(credit_manager_addr), abi=CREDIT_MANAGER_ABI
        # )
    
    @classmethod
    def from_chain(cls, chain_id: int = TESTNET_CHAIN_ID, private_key: Optional[str] = None) -> "Client":
        """Create a client for a specific chain"""
        return cls(private_key=private_key, chain_id=chain_id)
    
    @classmethod
    def from_chain_name(cls, chain_name: str = "testnet", private_key: Optional[str] = None) -> "Client":
        """Create a client from a chain name (testnet, localnet, devnet)"""
        chain_map = {
            "testnet": TESTNET_CHAIN_ID,
            "localnet": LOCALNET_CHAIN_ID,
            "devnet": DEVNET_CHAIN_ID,
        }
        
        if chain_name not in chain_map:
            raise ValueError(f"Unknown chain name: {chain_name}")
            
        return cls.from_chain(chain_map[chain_name], private_key)

    def get_chain_id(self) -> int:
        """Get the chain ID for the current network"""
        return self.w3.eth.chain_id

    def get_signer_address(self) -> ChecksumAddress:
        """Get the connected signer's address"""
        return self.signer.address

    def get_nonce(self) -> Nonce:
        """Get the nonce for the connected signer"""
        return self.w3.eth.get_transaction_count(self.signer.address)

    def wait_for_tx_receipt(self, tx_hash: HexBytes | HexBytes) -> TxReceipt:
        """Wait for a transaction receipt to be returned"""
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def parse_tx_receipt(self, contract: Contract, tx_receipt: TxReceipt, event_type: str) -> list[EventLog]:
        """Parse a transaction receipt for a given event type"""
        event = getattr(contract.events, event_type)()
        return event.process_receipt(tx_receipt, errors=EventLogErrorFlags.Discard)
    
    def get_subnet_id(self) -> SubnetId:
        """Get the subnet ID for the current client"""
        return self.subnet_id
        
    def switch_chain(self, chain_id: int) -> None:
        """
        Switch to a different chain
        
        Args:
            chain_id: Chain ID to switch to
        """
        self.evm_rpc_url = get_evm_rpc_url(chain_id)
        self.object_api_url = get_object_api_url(chain_id)
        self.chain_id = chain_id
        self.w3 = Web3(Web3.HTTPProvider(self.evm_rpc_url))
        
        self.subnet_id = SubnetId.from_chain(chain_id)

    def account_manager(self) -> AccountManager:
        """Get an account manager instance"""
        return AccountManager(self)

    def blob_manager(self, contract_address: Optional[str] = None) -> BlobManager:
        """Get a blob manager instance"""
        chain_id = self.get_chain_id()
        override = (
            contract_address or 
            self.contract_overrides.blob_manager.get(chain_id)
        )
        return BlobManager(self, override)

    def bucket_manager(self, contract_address: Optional[str] = None) -> BucketManager:
        """Get a bucket manager instance"""
        chain_id = self.get_chain_id()
        override = (
            contract_address or 
            self.contract_overrides.bucket_manager.get(chain_id)
        )
        return BucketManager(self, override)

    def credit_manager(self, contract_address: Optional[str] = None) -> CreditManager:
        """Get a credit manager instance"""
        chain_id = self.get_chain_id()
        override = (
            contract_address or 
            self.contract_overrides.credit_manager.get(chain_id)
        )
        return CreditManager(self, override)


if __name__ == "__main__":  # pragma: no cover
    pass
