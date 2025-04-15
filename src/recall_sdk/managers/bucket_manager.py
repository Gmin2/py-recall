import json
import mimetypes
import os
import re
from io import BytesIO
from typing import Any, Optional, Union

import requests
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from web3 import Web3
from web3.exceptions import ContractLogicError

from ..constants import (
    BUCKET_MANAGER_ABI,
    BUCKET_MANAGER_ADDRESS,
    IMACHINE_FACADE_ABI,
    MAX_OBJECT_LENGTH,
    MIN_TTL,
)
from ..exceptions import (
    ActorNotFoundError,
    BucketNotFoundError,
    ContractError,
    InvalidValueError,
    ObjectNotFoundError,
    UnexpectedError,
)
from ..types import BucketMetadata, CreateBucketResponse, ObjectValue, QueryResult
from .base_manager import BaseManager


def _raise_bucket_creation_failed():
    """Raise UnexpectedError for bucket creation failure."""
    raise UnexpectedError(UnexpectedError.BUCKET_CREATION_FAILED)


def _raise_object_not_found(bucket: str, key: str):
    """Raise ObjectNotFoundError."""
    raise ObjectNotFoundError(bucket, key)


def _raise_object_size_error(size: int, max_size: int):
    """Raise InvalidValueError for object size exceeds limit."""
    raise InvalidValueError(InvalidValueError.OBJECT_SIZE_EXCEEDS_LIMIT.format(size, max_size))


def _raise_ttl_error(min_ttl: int):
    """Raise InvalidValueError for TTL too low."""
    raise InvalidValueError(InvalidValueError.TTL_TOO_LOW.format(min_ttl))


def _raise_upload_failed(response_text: str):
    """Raise UnexpectedError for upload failure."""
    raise UnexpectedError(UnexpectedError.UPLOAD_FAILED.format(response_text))


def _raise_download_failed(response_text: str):
    """Raise UnexpectedError for download failure."""
    raise UnexpectedError(UnexpectedError.DOWNLOAD_FAILED.format(response_text))


def _raise_file_not_found(file_path: str):
    """Raise InvalidValueError for file not found."""
    raise InvalidValueError(InvalidValueError.FILE_NOT_FOUND.format(file_path))


def _raise_unsupported_file_type():
    """Raise InvalidValueError for unsupported file type."""
    raise InvalidValueError(InvalidValueError.UNSUPPORTED_FILE_TYPE)


def _raise_invalid_range(range_header: str):
    """Raise InvalidValueError for invalid range."""
    raise InvalidValueError(InvalidValueError.INVALID_RANGE.format(range_header))


class BucketManager(BaseManager):
    """
    Manager for bucket operations

    Provides methods to create, list, and manage buckets and their objects
    on the Recall Network.
    """

    def __init__(self, client: Any, contract_address: Optional[str] = None) -> None:
        """
        Initialize the BucketManager

        Args:
            client: The Recall client instance
            contract_address: Optional override for the contract address
        """
        super().__init__(client, contract_address)
        self.contract = self.get_contract(BUCKET_MANAGER_ABI, BUCKET_MANAGER_ADDRESS)

    def create(
        self, owner: Optional[ChecksumAddress] = None, metadata: Optional[dict[str, str]] = None
    ) -> CreateBucketResponse:
        """
        Create a bucket for a given owner or default to the signer's address

        Args:
            owner: Ethereum address of the bucket owner (defaults to signer)
            metadata: Optional metadata for the bucket

        Returns:
            CreateBucketResponse: Information about the created bucket

        Raises:
            ContractError: If the contract interaction fails
            ActorNotFoundError: If the actor is not found
            UnexpectedError: For unexpected errors
        """
        try:
            # Function arguments
            metadata_list = []
            if metadata:
                metadata_list = [(key, str(value)) for key, value in metadata.items()]

            if owner is None:
                owner = self.client.signer.address

            owner_address = to_checksum_address(owner)

            # Get contract gas estimate
            gas = self.contract.functions.createBucket(
                owner_address,
                metadata_list,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.createBucket(
                owner_address,
                metadata_list,
            ).build_transaction({
                "from": self.client.signer.address,
                "gas": gas,
                "maxFeePerGas": Web3.to_wei(100, "gwei"),
                "maxPriorityFeePerGas": Web3.to_wei(2, "gwei"),
                "nonce": self.w3.eth.get_transaction_count(self.client.signer.address),
            })

            # Sign and send transaction
            signed_tx = self.client.signer.sign_transaction(tx)

            # Send raw transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            # Parse events
            machine_facade_contract = self.w3.eth.contract(
                address=to_checksum_address(BUCKET_MANAGER_ADDRESS[self.w3.eth.chain_id]),
                abi=IMACHINE_FACADE_ABI,
            )

            machine_initialized_events = machine_facade_contract.events.MachineInitialized().process_receipt(receipt)

            if not machine_initialized_events:
                _raise_bucket_creation_failed()

            machine_initialized_event = machine_initialized_events[0]

            return CreateBucketResponse(
                bucket=machine_initialized_event.args.machineAddress,
                kind=machine_initialized_event.args.kind,
            )

        except ContractLogicError as e:
            if "actor not found" in str(e).lower():
                raise ActorNotFoundError(str(e)) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(str(e)) from e

    def lists(
        self, owner: Optional[ChecksumAddress] = None, block_number: Optional[int] = None
    ) -> list[BucketMetadata]:
        """
        list buckets for a given owner or default to the signer's address

        Args:
            owner: Ethereum address of the bucket owner (defaults to signer)
            block_number: Optional block number to query at

        Returns:
            list[BucketMetadata]: list of buckets owned by the address

        Raises:
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            if owner is None:
                owner = self.client.signer.address

            owner_address = to_checksum_address(owner)

            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            buckets = self.contract.functions.listBuckets(owner_address).call(**call_params)

            # Transform the response into a more usable format
            result = []
            for bucket in buckets:
                metadata_dict = {}
                for kv in bucket[2]:  # bucket[2] contains the metadata array
                    metadata_dict[kv[0]] = kv[1]

                result.append(
                    BucketMetadata(
                        kind=bucket[0],
                        addr=bucket[1],
                        metadata=metadata_dict,
                    )
                )
        except ContractLogicError as e:
            if "actor not found" in str(e).lower():
                # Return empty list if actor not found, mimicking JS SDK behavior
                return []
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(str(e)) from e

        return result

    def add_inner(self, bucket: ChecksumAddress, add_params: dict[str, Any]) -> dict[str, Any]:
        """
        Internal method to add an object to a bucket

        Args:
            bucket: Address of the bucket
            add_params: Parameters for adding the object

        Returns:
            dict[str, Any]: Transaction receipt information

        Raises:
            ContractError: If the contract interaction fails
            ActorNotFoundError: If the actor is not found
            UnexpectedError: For unexpected errors
        """
        try:
            bucket_address = to_checksum_address(bucket)

            # Get contract gas estimate
            gas = self.contract.functions.addObject(
                bucket_address,
                add_params,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.addObject(
                bucket_address,
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
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(UnexpectedError.ADD_OBJECT_FAILED.format(str(e))) from e

    def _prepare_add_params(
        self, key: str, data: bytes, content_type: Optional[str], size: int, options: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Prepare parameters for adding an object

        Args:
            key: Object key
            data: Object data
            content_type: Content type
            size: Object size
            options: Additional options

        Returns:
            dict[str, Any]: Prepared parameters

        Raises:
            InvalidValueError: If parameters are invalid
            UnexpectedError: For unexpected errors
        """
        metadata_raw = options.get("metadata", {})
        if content_type:
            metadata_raw["content-type"] = content_type

        # Convert metadata to list format for contract
        metadata_list = []
        for key_name, value in metadata_raw.items():
            metadata_list.append((key_name, str(value)))

        # Get node info from objects API
        try:
            node_response = requests.get(f"{self.client.object_api_url}/v1/node", timeout=30)
            node_data = node_response.json()
            source = node_data.get("node_id", "")
        except Exception as e:
            raise UnexpectedError(UnexpectedError.GET_NODE_INFO_FAILED.format(str(e))) from e

        # Validate size
        if size > MAX_OBJECT_LENGTH:
            _raise_object_size_error(size, MAX_OBJECT_LENGTH)

        # Handle TTL
        ttl = options.get("ttl", 0)
        if ttl != 0 and ttl < MIN_TTL:
            _raise_ttl_error(MIN_TTL)

        # Upload file to objects API
        try:
            form_data = {"size": str(size)}
            files = {"data": (key, data, content_type or "application/octet-stream")}
            upload_response = requests.post(
                f"{self.client.object_api_url}/v1/objects",
                data=form_data,
                files=files,
                timeout=60,  # Longer timeout for uploads
            )

            if not upload_response.ok:
                _raise_upload_failed(upload_response.text)

            upload_data = upload_response.json()
            blob_hash = upload_data.get("hash", "")
            metadata_hash = upload_data.get("metadata_hash", "")
        except requests.RequestException as e:
            raise UnexpectedError(UnexpectedError.UPLOAD_FAILED.format(str(e))) from e

        # Prepare parameters for the contract call
        return {
            "source": source,
            "key": key,
            "blobHash": blob_hash,
            "recoveryHash": metadata_hash,
            "size": size,
            "ttl": ttl,
            "metadata": metadata_list,
            "overwrite": options.get("overwrite", False),
            "from": self.client.signer.address,
        }

    def add(
        self,
        bucket: ChecksumAddress,
        key: str,
        file_data: Union[str, bytes, BytesIO],
        options: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Add an object to a bucket

        Args:
            bucket: Address of the bucket
            key: Object key (path)
            file_data: File data to upload (path, bytes, or file-like object)
            options: Optional parameters like ttl, metadata, overwrite

        Returns:
            dict[str, Any]: Transaction receipt information

        Raises:
            InvalidValueError: If the parameters are invalid
            ContractError: If the contract interaction fails
            ActorNotFoundError: If the actor is not found
            UnexpectedError: For unexpected errors
        """
        options = options or {}

        try:
            # Handle file data
            data, content_type, size = self._process_file_data(file_data)

            # Prepare parameters
            add_params = self._prepare_add_params(key, data, content_type, size, options)

            # Call the inner method to add the object
            return self.add_inner(bucket, add_params)

        except (ContractError, ActorNotFoundError, InvalidValueError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            raise UnexpectedError(UnexpectedError.ADD_OBJECT_FAILED.format(str(e))) from e

    def delete(self, bucket: ChecksumAddress, key: str) -> dict[str, Any]:
        """
        Delete an object from a bucket

        Args:
            bucket: Address of the bucket
            key: Object key to delete

        Returns:
            dict[str, Any]: Transaction receipt information

        Raises:
            BucketNotFoundError: If the bucket does not exist
            ObjectNotFoundError: If the object does not exist
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            bucket_address = to_checksum_address(bucket)

            # Get contract gas estimate
            gas = self.contract.functions.deleteObject(
                bucket_address,
                key,
                self.client.signer.address,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.deleteObject(
                bucket_address,
                key,
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
            if "object not found" in error_msg:
                raise ObjectNotFoundError(bucket, key) from e
            # Assume bucket not found for other contract reversion errors
            if "revert" in error_msg:
                raise BucketNotFoundError(bucket) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(UnexpectedError.DELETE_OBJECT_FAILED.format(str(e))) from e

    def get_object_value(self, bucket: ChecksumAddress, key: str, block_number: Optional[int] = None) -> ObjectValue:
        """
        Get object metadata without downloading the object

        Args:
            bucket: Address of the bucket
            key: Object key
            block_number: Optional block number to query at

        Returns:
            ObjectValue: Object metadata

        Raises:
            ObjectNotFoundError: If the object does not exist
            BucketNotFoundError: If the bucket does not exist
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            bucket_address = to_checksum_address(bucket)

            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            # Call contract to get object value
            result = self.contract.functions.getObject(bucket_address, key).call(**call_params)

            if not result or not result[0]:  # Check if blobHash is empty
                _raise_object_not_found(bucket, key)

            # Transform contract response to ObjectValue
            metadata_dict = {}
            for kv in result[4]:  # result[4] contains the metadata array
                metadata_dict[kv[0]] = kv[1]

            return ObjectValue(
                blobHash=result[0],
                recoveryHash=result[1],
                size=result[2],
                expiry=result[3],
                metadata=metadata_dict,
            )

        except ContractLogicError as e:
            if "object not found" in str(e).lower():
                raise ObjectNotFoundError(bucket, key) from e
            # Assume bucket not found for other contract reversion errors
            if "revert" in str(e).lower():
                raise BucketNotFoundError(bucket) from e
            raise ContractError(str(e)) from e
        except ObjectNotFoundError:
            # Re-raise ObjectNotFoundError
            raise
        except Exception as e:
            raise UnexpectedError(UnexpectedError.GET_OBJECT_VALUE_FAILED.format(str(e))) from e

    def _get_object_data(self, bucket: str, key: str, options: dict[str, Any]) -> bytes:
        """
        Download object data from the objects API

        Args:
            bucket: Address of the bucket
            key: Object key
            options: Additional options

        Returns:
            bytes: Object data

        Raises:
            BucketNotFoundError: If the bucket does not exist
            ObjectNotFoundError: If the object does not exist
            InvalidValueError: If parameters are invalid
            UnexpectedError: For unexpected errors
        """
        # Prepare request URL
        url = f"{self.client.object_api_url}/v1/objects/{bucket}/{key}"

        # Prepare headers (for range requests)
        headers = {}
        if "range" in options:
            range_option = options["range"]
            start = range_option.get("start", "")
            end = range_option.get("end", "")
            headers["Range"] = f"bytes={start}-{end}"

        # Add block height parameter if specified
        params = {}
        if "block_number" in options:
            params["height"] = str(options["block_number"])

        # Make request
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
        except requests.RequestException as e:
            raise UnexpectedError(UnexpectedError.NETWORK_REQUEST_FAILED.format(str(e))) from e

        if not response.ok:
            # Handle error responses
            try:
                error_data = response.json()
                error_message = error_data.get("message", "")

                if "actor does not exist" in error_message:
                    raise BucketNotFoundError(bucket) from None
                elif "is not available" in error_message:
                    # Extract blob hash from error message if possible
                    # Not using the blob_hash variable to avoid F841 error
                    re.search(r"object\s+(.*)\s+is not available", error_message)
                    raise ObjectNotFoundError(bucket, key) from None
                elif "invalid range" in error_message:
                    _raise_invalid_range(headers.get("Range", ""))

            except json.JSONDecodeError:
                # If error isn't JSON, just use the text
                pass

            _raise_download_failed(response.text)

        return response.content

    def get(
        self,
        bucket: ChecksumAddress,
        key: str,
        options: Optional[dict[str, Any]] = None,
    ) -> bytes:
        """
        Get an object from a bucket

        Args:
            bucket: Address of the bucket
            key: Object key
            options: Optional parameters like range and block_number

        Returns:
            bytes: Object data

        Raises:
            ObjectNotFoundError: If the object does not exist
            BucketNotFoundError: If the bucket does not exist
            InvalidValueError: If the range is invalid
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        options = options or {}
        bucket_address = to_checksum_address(bucket)

        try:
            # Verify object exists (will raise ObjectNotFoundError if not found)
            self.get_object_value(bucket_address, key, options.get("block_number"))

            # Get object data
            return self._get_object_data(bucket_address, key, options)

        except (ObjectNotFoundError, BucketNotFoundError, InvalidValueError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            raise UnexpectedError(UnexpectedError.GET_OBJECT_FAILED.format(str(e))) from e

    def get_stream(
        self,
        bucket: ChecksumAddress,
        key: str,
        range_options: Optional[dict[str, int]] = None,
        block_number: Optional[int] = None,
    ) -> BytesIO:
        """
        Get a file-like object stream of an object from a bucket

        Args:
            bucket: Address of the bucket
            key: Object key
            range_options: Optional range parameters with start and end
            block_number: Optional block number to query at

        Returns:
            BytesIO: File-like object containing the data

        Raises:
            ObjectNotFoundError: If the object does not exist
            BucketNotFoundError: If the bucket does not exist
            InvalidValueError: If the range is invalid
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        options = {}
        if range_options:
            options["range"] = range_options
        if block_number is not None:
            options["block_number"] = block_number

        data = self.get(bucket, key, options)
        return BytesIO(data)

    def _process_query_result(self, result: list[Any]) -> dict[str, Any]:
        """
        Process query results into a more usable format

        Args:
            result: Raw query result from the contract

        Returns:
            dict[str, Any]: Processed query result
        """
        objects = []
        for obj in result[0]:  # result[0] contains the objects array
            # Convert metadata to dictionary
            metadata_dict = {}
            for kv in obj[1][3]:  # obj[1][3] contains the metadata array
                metadata_dict[kv[0]] = kv[1]

            objects.append({
                "key": obj[0],
                "state": {
                    "blobHash": obj[1][0],
                    "size": obj[1][1],
                    "expiry": obj[1][2],
                    "metadata": metadata_dict,
                },
            })

        return {
            "objects": objects,
            "commonPrefixes": result[1],
            "nextKey": result[2],
        }

    def query(
        self,
        bucket: ChecksumAddress,
        options: Optional[dict[str, Any]] = None,
    ) -> QueryResult:
        """
        Query objects in a bucket with filtering options

        Args:
            bucket: Address of the bucket
            options: Query options (prefix, delimiter, startKey, limit, block_number)

        Returns:
            QueryResult: Query results containing objects and common prefixes

        Raises:
            BucketNotFoundError: If the bucket does not exist
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            options = options or {}
            bucket_address = to_checksum_address(bucket)

            # Default values
            prefix = options.get("prefix", "")
            delimiter = options.get("delimiter", "/")
            start_key = options.get("startKey", "")
            limit = options.get("limit", 100)

            # Add block number to call if provided
            call_params = {}
            if "block_number" in options:
                call_params["block_identifier"] = options["block_number"]

            # Call appropriate contract function based on provided parameters
            result = self._call_query_function(bucket_address, prefix, delimiter, start_key, limit, call_params)

            # Process the result
            processed_result = self._process_query_result(result)

            return QueryResult(**processed_result)

        except ContractLogicError as e:
            # Assume bucket not found for contract reversion errors
            if "revert" in str(e).lower():
                raise BucketNotFoundError(bucket) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(UnexpectedError.QUERY_BUCKET_FAILED.format(str(e))) from e

    def _call_query_function(
        self,
        bucket_address: ChecksumAddress,
        prefix: str,
        delimiter: str,
        start_key: str,
        limit: int,
        call_params: dict[str, Any],
    ) -> Any:
        """
        Call the appropriate queryObjects function based on parameters

        Args:
            bucket_address: Address of the bucket
            prefix: Prefix to filter objects by
            delimiter: Delimiter for common prefixes
            start_key: Key to start query from
            limit: Maximum number of objects to return
            call_params: Additional call parameters

        Returns:
            Any: Raw contract call result
        """
        if prefix and delimiter and start_key and limit:
            return self.contract.functions.queryObjects(bucket_address, prefix, delimiter, start_key, limit).call(
                **call_params
            )
        elif prefix and delimiter and start_key:
            return self.contract.functions.queryObjects(bucket_address, prefix, delimiter, start_key).call(
                **call_params
            )
        elif prefix and delimiter:
            return self.contract.functions.queryObjects(bucket_address, prefix, delimiter).call(**call_params)
        elif prefix:
            return self.contract.functions.queryObjects(bucket_address, prefix).call(**call_params)
        else:
            return self.contract.functions.queryObjects(bucket_address).call(**call_params)

    def _process_file_data(self, file_data: Union[str, bytes, BytesIO]) -> tuple[bytes, Optional[str], int]:
        """
        Process file data from various sources

        Args:
            file_data: File data (path, bytes, or file-like object)

        Returns:
            tuple[bytes, Optional[str], int]: Processed data, content type, and size

        Raises:
            InvalidValueError: If file data is invalid
            UnexpectedError: For unexpected errors
        """
        try:
            content_type = None

            # Handle file path string
            if isinstance(file_data, str):
                if not os.path.exists(file_data):
                    _raise_file_not_found(file_data)

                content_type, _ = mimetypes.guess_type(file_data)
                with open(file_data, "rb") as f:
                    data = f.read()
                return data, content_type, len(data)

            # Handle bytes
            elif isinstance(file_data, bytes):
                return file_data, None, len(file_data)

            # Handle file-like object
            elif hasattr(file_data, "read"):
                data = file_data.read()
                if isinstance(data, str):
                    data = data.encode("utf-8")
                return data, None, len(data)

            else:
                _raise_unsupported_file_type()

        except (OSError, InvalidValueError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            raise UnexpectedError(UnexpectedError.PROCESS_FILE_DATA_FAILED.format(str(e))) from e
