"""
Recall client and wrapper contract interactions
"""

from typing import Optional, TypeVar

from eth_account.account import LocalAccount
from web3 import Account, Web3
from web3.contract import Contract

from .constants import (
    TESTNET_CHAIN_ID,
    get_evm_rpc_url,
    get_object_api_url,
)
from .managers import (
    BlobManager,
    BucketManager,
    CreditManager,
)

T = TypeVar("T")


class Client:
    """
    Recall client and wrapper contract interactions
    """

    w3: Web3
    signer: LocalAccount
    evm_rpc_url: str
    object_api_url: str
    blob_manager: Contract
    bucket_manager: Contract
    credit_manager: Contract
    _contract_overrides: Optional[dict[str, str]] = (None,)

    def __init__(
        self,
        private_key: str,
        chain_id: int = TESTNET_CHAIN_ID,
        evm_rpc_url: Optional[str] = None,
        object_api_url: Optional[str] = None,
        contract_overrides: Optional[dict[str, str]] = None,
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
        self._contract_overrides = {} if contract_overrides is None else contract_overrides

    def bucket_manager(self, contract_address: Optional[str] = None) -> BucketManager:
        """Get a bucket manager instance"""
        override = contract_address
        if not override and hasattr(self, "_contract_overrides") and isinstance(self._contract_overrides, dict):
            override = self._contract_overrides.get("bucket_manager")
        return BucketManager(self, override)

    def credit_manager(self, contract_address: Optional[str] = None) -> CreditManager:
        """Get a credit manager instance"""
        override = contract_address
        if not override and hasattr(self, "_contract_overrides") and isinstance(self._contract_overrides, dict):
            override = self._contract_overrides.get("credit_manager")
        return CreditManager(self, override)

    def blob_manager(self, contract_address: Optional[str] = None) -> BlobManager:
        """Get a blob manager instance"""
        override = contract_address
        if not override and hasattr(self, "_contract_overrides") and isinstance(self._contract_overrides, dict):
            override = self._contract_overrides.get("blob_manager")
        return BlobManager(self, override)
