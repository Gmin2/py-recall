"""
Bucket manager for Recall network storage operations
"""

from typing import Any, Dict, List, Optional, Union, cast

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError

from ..constants import (
    BUCKET_MANAGER_ABI, 
    BUCKET_MANAGER_ADDRESS,
    IMACHINE_FACADE_ABI
)
from ..exceptions import ContractError, UnexpectedError
from ..types import CreatedBucketResponse, Result

class BucketManager:
    """
    Manager for bucket operations in the Recall network
    """
    
    def __init__(self, client, contract_address: Optional[str] = None):
        """
        Initialize the bucket manager
        
        Args:
            client: Recall client instance
            contract_address: Optional contract address override
        """
        self.client = client
        chain_id = client.get_chain_id()
        
        # Use provided address or get default for this chain
        address = contract_address or BUCKET_MANAGER_ADDRESS.get(chain_id)
        if not address:
            raise ValueError(f"No bucket manager address for chain ID {chain_id}")
        
        # Create contract instance
        self.contract = client.w3.eth.contract(
            address=to_checksum_address(address),
            abi=BUCKET_MANAGER_ABI
        )
    
    def get_contract(self) -> Contract:
        """Return the underlying contract instance"""
        return self.contract