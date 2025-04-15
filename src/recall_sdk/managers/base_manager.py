from eth_utils import to_checksum_address

from ..exceptions import ContractError


class BaseManager:
    """Base class for all manager implementations"""

    def __init__(self, client, contract_address=None):
        self.client = client
        self.w3 = client.w3
        self.contract_address = contract_address

    def get_contract(self, abi, address_mapping):
        """Get contract instance with appropriate address"""
        chain_id = self.w3.eth.chain_id

        # Use override address if provided
        if self.contract_address:
            address = self.contract_address
        else:
            # Use default address for the chain
            if chain_id not in address_mapping:
                raise ContractError(ContractError.CONTRACT_ADDRESS_NOT_FOUND.format(chain_id))
            address = address_mapping[chain_id]

        return self.w3.eth.contract(address=to_checksum_address(address), abi=abi)
