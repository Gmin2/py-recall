"""
Credit manager for Recall network operations
"""

from typing import Any, Dict, List, Optional, Union, cast

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError

from ..constants import (
    CREDIT_MANAGER_ABI, 
    CREDIT_MANAGER_ADDRESS
)
from ..exceptions import ContractError, UnexpectedError
from ..types import Result

class CreditManager:
    """
    Manager for credit operations in the Recall network
    """
    
    def __init__(self, client, contract_address: Optional[str] = None):
        """
        Initialize the credit manager
        
        Args:
            client: Recall client instance
            contract_address: Optional contract address override
        """
        self.client = client
        chain_id = client.get_chain_id()
        
        # Use provided address or get default for this chain
        address = contract_address or CREDIT_MANAGER_ADDRESS.get(chain_id)
        if not address:
            raise ValueError(f"No credit manager address for chain ID {chain_id}")
        
        # Create contract instance
        self.contract = client.w3.eth.contract(
            address=to_checksum_address(address),
            abi=CREDIT_MANAGER_ABI
        )
    
    def get_contract(self) -> Contract:
        """Return the underlying contract instance"""
        return self.contract