import requests
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.exceptions import ContractLogicError

from ..constants import (
    BLOB_MANAGER_ABI,
    BLOB_MANAGER_ADDRESS,
    MIN_TTL,
)
from ..exceptions import (
    ActorNotFoundError,
    AddBlobError,
    BlobNotFoundError,
    ContractError,
    DeleteBlobError,
    InvalidValueError,
    OverwriteBlobError,
    UnexpectedError,
)
from ..types import (
    AddBlobOptions,
    Blob,
    BlobTuple,
    StorageStats,
    SubnetStats,
    Subscriber,
    BlobSourceInfo,
)
from .base_manager import BaseManager

from typing import Any, Optional

class BlobManager(BaseManager):
    """
    Manager for blob operations

    Provides methods to create, manage, and query blobs on the Recall Network.
    """

    def __init__(self, client: Any, contract_address: Optional[str] = None) -> None:
        """
        Initialize the BlobManager

        Args:
            client: The Recall client instance
            contract_address: Optional override for the contract address
        """
        super().__init__(client, contract_address)
        self.contract = self.get_contract(BLOB_MANAGER_ABI, BLOB_MANAGER_ADDRESS)

    def add_blob_inner(self, add_params: dict[str, Any]) -> dict[str, Any]:
        """
        Internal method to add a blob

        Args:
            add_params: Parameters for adding the blob

        Returns:
            dict[str, Any]: Transaction receipt information

        Raises:
            ActorNotFoundError: If the actor is not found
            AddBlobError: If adding the blob fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Get contract gas estimate
            gas = self.contract.functions.addBlob(
                add_params,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.addBlob(
                add_params,
            ).build_transaction({
                "from": self.client.signer.address,
                "gas": gas,
                "maxFeePerGas": Web3.to_wei(100, "gwei"),
                "maxPriorityFeePerGas": Web3.to_wei(2, "gwei"),
                "nonce": self.w3.eth.get_transaction_count(self.client.signer.address),
            })

            # Sign and send transaction
            signed_tx = self.client.signer.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return {
                "receipt": receipt,
                "transactionHash": receipt["transactionHash"].hex(),
            }

        except ContractLogicError as e:
            if "actor not found" in str(e).lower():
                raise ActorNotFoundError(str(e)) from e
            raise AddBlobError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to add blob: {str(e)}") from e

    def add_blob(
        self,
        blob_hash: str,
        subscription_id: str,
        size: int,
        options: Optional[AddBlobOptions] = None,
    ) -> dict[str, Any]:
        """
        Add a blob to the network

        Args:
            blob_hash: Hash of the blob
            subscription_id: Subscription ID for the blob
            size: Size of the blob in bytes
            options: Optional parameters like ttl, sponsor

        Returns:
            dict[str, Any]: Transaction receipt information

        Raises:
            InvalidValueError: If parameters are invalid
            ActorNotFoundError: If the actor is not found
            AddBlobError: If adding the blob fails
            UnexpectedError: For unexpected errors
        """
        options = options or {}
        ttl = options.get("ttl", 0)

        if ttl != 0 and ttl < MIN_TTL:
            raise InvalidValueError(InvalidValueError.TTL_TOO_LOW.format(MIN_TTL))

        try:
            # Get node info from objects API
            try:
                node_response = requests.get(f"{self.client.object_api_url}/v1/node", timeout=30)
                node_data = node_response.json()
                source = node_data.get("node_id", "")
            except Exception as e:
                raise UnexpectedError(UnexpectedError.GET_NODE_INFO_FAILED.format(str(e))) from e

            # Prepare add parameters
            add_params = {
                "sponsor": options.get("sponsor", "0x0000000000000000000000000000000000000000"),
                "source": source,
                "blobHash": blob_hash,
                "metadataHash": "",
                "subscriptionId": subscription_id,
                "size": size,
                "ttl": ttl,
                "from": self.client.signer.address,
            }

            return self.add_blob_inner(add_params)

        except (InvalidValueError, ActorNotFoundError, AddBlobError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            raise UnexpectedError(f"Failed to add blob: {str(e)}") from e

    def delete_blob(
        self,
        blob_hash: str,
        subscription_id: str,
        subscriber: Optional[ChecksumAddress] = None,
    ) -> dict[str, Any]:
        """
        Delete a blob from the network

        Args:
            blob_hash: Hash of the blob to delete
            subscription_id: Subscription ID for the blob
            subscriber: Optional subscriber address, defaults to zero address

        Returns:
            dict[str, Any]: Transaction receipt information

        Raises:
            BlobNotFoundError: If the blob is not found
            ActorNotFoundError: If the actor is not found
            DeleteBlobError: If deleting the blob fails
            UnexpectedError: For unexpected errors
        """
        try:
            subscriber_address = subscriber if subscriber else "0x0000000000000000000000000000000000000000"

            # Get contract gas estimate
            gas = self.contract.functions.deleteBlob(
                subscriber_address,
                blob_hash,
                subscription_id,
                self.client.signer.address,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.deleteBlob(
                subscriber_address,
                blob_hash,
                subscription_id,
                self.client.signer.address,
            ).build_transaction({
                "from": self.client.signer.address,
                "gas": gas,
                "maxFeePerGas": Web3.to_wei(100, "gwei"),
                "maxPriorityFeePerGas": Web3.to_wei(2, "gwei"),
                "nonce": self.w3.eth.get_transaction_count(self.client.signer.address),
            })

            # Sign and send transaction
            signed_tx = self.client.signer.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return {
                "receipt": receipt,
                "transactionHash": receipt["transactionHash"].hex(),
            }

        except ContractLogicError as e:
            error_msg = str(e).lower()
            if "blob not found" in error_msg:
                raise BlobNotFoundError(blob_hash) from e
            if "actor not found" in error_msg:
                raise ActorNotFoundError(str(e)) from e
            raise DeleteBlobError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to delete blob: {str(e)}") from e

    def get_blob(self, blob_hash: str, block_number: Optional[int] = None) -> Blob:
        """
        Get blob information

        Args:
            blob_hash: Hash of the blob
            block_number: Optional block number to query at

        Returns:
            Blob: Blob information

        Raises:
            BlobNotFoundError: If the blob is not found
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getBlob(blob_hash).call(**call_params)

            # Convert Solidity struct to Python dataclass
            subscribers = []
            for sub in result[2]:  # result[2] contains subscribers array
                subscribers.append(Subscriber(
                    subscriptionId=sub[0],
                    expiry=sub[1],
                ))

            return Blob(
                size=result[0],
                metadataHash=result[1],
                subscribers=subscribers,
                status=result[3],
            )

        except ContractLogicError as e:
            error_msg = str(e).lower()
            if "blob not found" in error_msg:
                raise BlobNotFoundError(blob_hash) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get blob: {str(e)}") from e

    def get_blob_status(
        self,
        subscriber: ChecksumAddress,
        blob_hash: str,
        subscription_id: str,
        block_number: Optional[int] = None,
    ) -> int:
        """
        Get the status of a blob

        Args:
            subscriber: Subscriber address
            blob_hash: Hash of the blob
            subscription_id: Subscription ID for the blob
            block_number: Optional block number to query at

        Returns:
            int: Blob status (0: unknown, 1: pending, 2: resolved)

        Raises:
            BlobNotFoundError: If the blob is not found
            ActorNotFoundError: If the actor is not found
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            subscriber_address = Web3.to_checksum_address(subscriber)

            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getBlobStatus(
                subscriber_address,
                blob_hash,
                subscription_id,
            ).call(**call_params)

            return result

        except ContractLogicError as e:
            error_msg = str(e).lower()
            if "blob not found" in error_msg:
                raise BlobNotFoundError(blob_hash) from e
            if "actor not found" in error_msg:
                raise ActorNotFoundError(str(e)) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get blob status: {str(e)}") from e

    def overwrite_blob_inner(self, old_hash: str, add_params: dict[str, Any]) -> dict[str, Any]:
        """
        Internal method to overwrite a blob

        Args:
            old_hash: Hash of the blob to overwrite
            add_params: Parameters for the new blob

        Returns:
            dict[str, Any]: Transaction receipt information

        Raises:
            BlobNotFoundError: If the blob is not found
            ActorNotFoundError: If the actor is not found
            OverwriteBlobError: If overwriting the blob fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Get contract gas estimate
            gas = self.contract.functions.overwriteBlob(
                old_hash,
                add_params,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.overwriteBlob(
                old_hash,
                add_params,
            ).build_transaction({
                "from": self.client.signer.address,
                "gas": gas,
                "maxFeePerGas": Web3.to_wei(100, "gwei"),
                "maxPriorityFeePerGas": Web3.to_wei(2, "gwei"),
                "nonce": self.w3.eth.get_transaction_count(self.client.signer.address),
            })

            # Sign and send transaction
            signed_tx = self.client.signer.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return {
                "receipt": receipt,
                "transactionHash": receipt["transactionHash"].hex(),
            }

        except ContractLogicError as e:
            error_msg = str(e).lower()
            if "blob not found" in error_msg:
                raise BlobNotFoundError(old_hash) from e
            if "actor not found" in error_msg:
                raise ActorNotFoundError(str(e)) from e
            raise OverwriteBlobError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to overwrite blob: {str(e)}") from e

    def overwrite_blob(
        self,
        old_hash: str,
        new_hash: str,
        subscription_id: str,
        size: int,
        options: Optional[AddBlobOptions] = None,
    ) -> dict[str, Any]:
        """
        Overwrite a blob

        Args:
            old_hash: Hash of the blob to overwrite
            new_hash: Hash of the new blob
            subscription_id: Subscription ID for the blob
            size: Size of the new blob in bytes
            options: Optional parameters like ttl, sponsor

        Returns:
            dict[str, Any]: Transaction receipt information

        Raises:
            InvalidValueError: If parameters are invalid
            BlobNotFoundError: If the blob is not found
            ActorNotFoundError: If the actor is not found
            OverwriteBlobError: If overwriting the blob fails
            UnexpectedError: For unexpected errors
        """
        options = options or {}
        ttl = options.get("ttl", 0)

        try:
            # Get node info from objects API
            try:
                node_response = requests.get(f"{self.client.object_api_url}/v1/node", timeout=30)
                node_data = node_response.json()
                source = node_data.get("node_id", "")
            except Exception as e:
                raise UnexpectedError(UnexpectedError.GET_NODE_INFO_FAILED.format(str(e))) from e

            # Prepare add parameters
            add_params = {
                "sponsor": options.get("sponsor", "0x0000000000000000000000000000000000000000"),
                "source": source,
                "blobHash": new_hash,
                "metadataHash": "",
                "subscriptionId": subscription_id,
                "size": size,
                "ttl": ttl,
                "from": self.client.signer.address,
            }

            return self.overwrite_blob_inner(old_hash, add_params)

        except (InvalidValueError, BlobNotFoundError, ActorNotFoundError, OverwriteBlobError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            raise UnexpectedError(f"Failed to overwrite blob: {str(e)}") from e

    def get_added_blobs(self, size: int, block_number: Optional[int] = None) -> list[BlobTuple]:
        """
        Get added blobs

        Args:
            size: Maximum number of blobs to return
            block_number: Optional block number to query at

        Returns:
            List[BlobTuple]: List of added blobs

        Raises:
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getAddedBlobs(size).call(**call_params)

            # Convert Solidity struct to Python dataclass
            blobs = []
            for blob in result:
                source_info = []
                for info in blob[1]:  # blob[1] contains sourceInfo array
                    source_info.append(BlobSourceInfo(
                        subscriber=info[0],
                        subscriptionId=info[1],
                        source=info[2],
                    ))

                blobs.append(BlobTuple(
                    blobHash=blob[0],
                    sourceInfo=source_info,
                ))

            return blobs

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get added blobs: {str(e)}") from e

    def get_pending_blobs(self, size: int, block_number: Optional[int] = None) -> list[BlobTuple]:
        """
        Get pending blobs

        Args:
            size: Maximum number of blobs to return
            block_number: Optional block number to query at

        Returns:
            List[BlobTuple]: List of pending blobs

        Raises:
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getPendingBlobs(size).call(**call_params)

            # Convert Solidity struct to Python dataclass
            blobs = []
            for blob in result:
                source_info = []
                for info in blob[1]:  # blob[1] contains sourceInfo array
                    source_info.append(BlobSourceInfo(
                        subscriber=info[0],
                        subscriptionId=info[1],
                        source=info[2],
                    ))

                blobs.append(BlobTuple(
                    blobHash=blob[0],
                    sourceInfo=source_info,
                ))

            return blobs

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get pending blobs: {str(e)}") from e

    def get_pending_blobs_count(self, block_number: Optional[int] = None) -> int:
        """
        Get the count of pending blobs

        Args:
            block_number: Optional block number to query at

        Returns:
            int: Count of pending blobs

        Raises:
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getPendingBlobsCount().call(**call_params)
            return result

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get pending blobs count: {str(e)}") from e

    def get_pending_bytes_count(self, block_number: Optional[int] = None) -> int:
        """
        Get the count of pending bytes

        Args:
            block_number: Optional block number to query at

        Returns:
            int: Count of pending bytes

        Raises:
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getPendingBytesCount().call(**call_params)
            return result

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get pending bytes count: {str(e)}") from e

    def get_storage_stats(self, block_number: Optional[int] = None) -> StorageStats:
        """
        Get storage statistics

        Args:
            block_number: Optional block number to query at

        Returns:
            StorageStats: Storage statistics

        Raises:
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getStorageStats().call(**call_params)

            return StorageStats(
                capacityFree=result[0],
                capacityUsed=result[1],
                numBlobs=result[2],
                numResolving=result[3],
                numAccounts=result[4],
                bytesResolving=result[5],
                numAdded=result[6],
                bytesAdded=result[7],
            )

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get storage stats: {str(e)}") from e

    def get_storage_usage(self, address: Optional[ChecksumAddress] = None, block_number: Optional[int] = None) -> int:
        """
        Get storage usage for an address

        Args:
            address: Address to get storage usage for, defaults to signer
            block_number: Optional block number to query at

        Returns:
            int: Storage usage in bytes

        Raises:
            ActorNotFoundError: If the actor is not found
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            addr = address if address else self.client.signer.address
            addr_checksum = Web3.to_checksum_address(addr)

            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getStorageUsage(addr_checksum).call(**call_params)
            return result

        except ContractLogicError as e:
            error_msg = str(e).lower()
            if "actor not found" in error_msg:
                raise ActorNotFoundError(str(e)) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get storage usage: {str(e)}") from e

    def get_subnet_stats(self, block_number: Optional[int] = None) -> SubnetStats:
        """
        Get subnet statistics

        Args:
            block_number: Optional block number to query at

        Returns:
            SubnetStats: Subnet statistics

        Raises:
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            result = self.contract.functions.getSubnetStats().call(**call_params)

            return SubnetStats(
                balance=result[0],
                capacityFree=result[1],
                capacityUsed=result[2],
                creditSold=result[3],
                creditCommitted=result[4],
                creditDebited=result[5],
                tokenCreditRate=result[6],
                numAccounts=result[7],
                numBlobs=result[8],
                numAdded=result[9],
                bytesAdded=result[10],
                numResolving=result[11],
                bytesResolving=result[12],
            )

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get subnet stats: {str(e)}") from e
