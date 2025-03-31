"""Address handling for Filecoin Ethereum-style addresses."""
import re
from typing import Optional


class NetworkPrefix:
    """Network prefixes for Filecoin addresses."""
    Mainnet = "f"
    Testnet = "t"


class FilEthAddress:
    """Filecoin Ethereum address handling."""
    
    @classmethod
    def from_string(cls, address_str: str) -> 'FilEthAddress':
        """Create a FilEthAddress instance from a string.
        
        Args:
            address_str: A Filecoin address string like 'f410...'
            
        Returns:
            A new FilEthAddress instance
        """
        # This is a simplified implementation that only supports
        # the functionality needed for ActorNotFoundResult
        return cls(address_str)
    
    def __init__(self, address_str: str):
        """Initialize a FilEthAddress.
        
        Args:
            address_str: A Filecoin address string
        """
        self.address_str = address_str
        
    def to_eth_address_hex(self, hex_prefix: bool = True) -> str:
        """Convert to Ethereum address format.
        
        Args:
            hex_prefix: Whether to include 0x prefix
            
        Returns:
            Ethereum address in hex format
        """
        # This is a simplified implementation that creates a dummy ETH address
        # In a real implementation, this would properly convert the Filecoin address
        # to an Ethereum address format
        prefix = "0x" if hex_prefix else ""
        # Just convert to a reasonable format for demonstration
        return f"{prefix}0000000000000000000000000000000000000000"


def is_actor_not_found_error(error: Exception) -> dict:
    """Check if an error indicates an actor not found condition.
    
    Args:
        error: The exception to check
        
    Returns:
        A dictionary with is_actor_not_found and address keys
    """
    error_message = str(error)
    is_actor_not_found = "actor::resolve_address -- actor not found" in error_message
    
    address = None
    if is_actor_not_found:
        address_match = re.search(r'f410[a-z0-9]+', error_message, re.IGNORECASE)
        if address_match:
            # Convert the found address to an Ethereum-style hex address
            fil_address = FilEthAddress.from_string(address_match.group(0))
            address = fil_address.to_eth_address_hex()
    
    return {
        "is_actor_not_found": is_actor_not_found,
        "address": address
    }


class ActorNotFound(Exception):
    """Exception raised when an actor is not found."""

    def __init__(self, address: str):
        message = f"Actor not found (hint: ensure the address is registered: '{address}')"
        self.name = "ActorNotFound"
        super().__init__(message)