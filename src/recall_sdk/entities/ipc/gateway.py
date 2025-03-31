"""
Gateway manager for Recall network IPC operations
"""

from typing import Any, Optional

from web3 import Web3
from web3.contract import Contract
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address

from ...constants import GATEWAY_MANAGER_FACET_ABI
from ...types import Result

class GatewayManager:
    """
    Manager for gateway operations in the Recall network
    """
    
    def __init__(self):
        """Initialize the gateway manager"""
        pass
    
    def get_contract(self, w3: Web3, contract_address: str) -> Contract:
        """
        Get the gateway manager contract
        
        Args:
            w3: Web3 instance
            contract_address: Contract address
            
        Returns:
            Contract instance
        """
        return w3.eth.contract(
            address=to_checksum_address(contract_address),
            abi=GATEWAY_MANAGER_FACET_ABI
        )