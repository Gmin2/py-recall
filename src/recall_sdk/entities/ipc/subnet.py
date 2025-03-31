"""
Subnet ID utilities for Recall network
"""

from typing import List, Optional

from ...constants import (
    TESTNET_CHAIN_ID,
    TESTNET_SUBNET_ID,
    LOCALNET_CHAIN_ID, 
    LOCALNET_SUBNET_ID,
    DEVNET_CHAIN_ID,
    DEVNET_SUBNET_ID
)

class SubnetId:
    """
    Subnet ID representation
    """
    
    def __init__(self, root: int, route: List[str], chain_id: Optional[int] = None, faux: str = ""):
        """
        Initialize the subnet ID
        
        Args:
            root: Root ID
            route: Route path
            chain_id: Optional explicit chain ID
            faux: Optional string representation
        """
        self.root = root
        self.route = route
        self.explicit_chain_id = chain_id
        self.faux = faux
    
    @classmethod
    def from_string(cls, subnet_id_str: str) -> "SubnetId":
        """
        Create a subnet ID from a string
        
        Args:
            subnet_id_str: Subnet ID string
            
        Returns:
            SubnetId instance
        """
        if not subnet_id_str.startswith("/r"):
            return cls(0, [], None, subnet_id_str)
            
        parts = subnet_id_str.split("/")
        if len(parts) < 3:
            return cls(0, [], None, subnet_id_str)
            
        root_str = parts[1]
        root = int(root_str[1:])  # Remove 'r' prefix
        route = parts[2:] if len(parts) > 2 else []
        
        # Map to known chain IDs
        chain_id = None
        if subnet_id_str == TESTNET_SUBNET_ID:
            chain_id = TESTNET_CHAIN_ID
        elif subnet_id_str == LOCALNET_SUBNET_ID:
            chain_id = LOCALNET_CHAIN_ID
        elif subnet_id_str == DEVNET_SUBNET_ID:
            chain_id = DEVNET_CHAIN_ID
            
        return cls(root, route, chain_id, subnet_id_str)
    
    @classmethod
    def from_chain(cls, chain_id: int) -> "SubnetId":
        """
        Create a subnet ID from a chain ID
        
        Args:
            chain_id: Chain ID
            
        Returns:
            SubnetId instance
        """
        if chain_id == TESTNET_CHAIN_ID:
            return cls.from_string(TESTNET_SUBNET_ID)
        elif chain_id == LOCALNET_CHAIN_ID:
            return cls.from_string(LOCALNET_SUBNET_ID)
        elif chain_id == DEVNET_CHAIN_ID:
            return cls.from_string(DEVNET_SUBNET_ID)
        else:
            raise ValueError(f"Unknown chain ID: {chain_id}")
    
    def chain_id(self) -> int:
        """
        Get the chain ID for this subnet ID
        
        Returns:
            Chain ID
        """
        if self.explicit_chain_id is not None:
            return self.explicit_chain_id
            
        # Compute chain ID based on subnet ID string
        # In a real implementation, this would use a hash function
        # similar to the JavaScript implementation
        return self.root
    
    def toString(self) -> str:
        """
        Get string representation of this subnet ID
        
        Returns:
            String representation
        """
        if self.faux:
            return self.faux
            
        if not self.route:
            return f"/r{self.root}"
            
        route_str = "/".join(self.route)
        return f"/r{self.root}/{route_str}"