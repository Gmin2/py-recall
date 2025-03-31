"""
Account manager for Recall network operations
"""

from typing import Any, Dict, List, Optional, Union, cast

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError

from ..constants import (
    GATEWAY_MANAGER_FACET_ABI,
    GATEWAY_MANAGER_FACET_ADDRESS,
    IERC20_ABI,
    SUPPLY_SOURCE_ADDRESS
)
from ..exceptions import ContractError, UnexpectedError
from ..types import Result
from .ipc.gateway import GatewayManager

class AccountManager:
    """
    Manager for account operations in the Recall network
    """
    
    def __init__(self, client):
        """
        Initialize the account manager
        
        Args:
            client: Recall client instance
        """
        self.client = client
        self.gateway_manager = GatewayManager()
    
    def get_gateway_manager(self) -> GatewayManager:
        """Get the gateway manager instance"""
        return self.gateway_manager
    
    def get_supply_source(self, chain, contract_address: Optional[str] = None) -> Contract:
        """
        Get the supply source contract
        
        Args:
            chain: Chain to use for the contract
            contract_address: Optional contract address override
            
        Returns:
            Contract instance
        """
        chain_id = chain if isinstance(chain, int) else chain.id
        
        # Get default address for this chain
        default_address = SUPPLY_SOURCE_ADDRESS.get(chain_id)
        
        # Use override from client if available
        override_config = self.client.contract_overrides.account_manager.get("recall_erc20", {})
        override_address = override_config.get(chain_id)
        
        # Determine which address to use
        address = contract_address or override_address or default_address
        if not address:
            raise ValueError(f"No supply source address for chain ID {chain_id}")
        
        # Create and return contract
        return self.client.w3.eth.contract(
            address=to_checksum_address(address),
            abi=IERC20_ABI
        )