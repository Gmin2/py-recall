"""Recall SDK exceptions."""


class RecallError(Exception):
    """Base exception for all Recall SDK errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ContractError(RecallError):
    """Exception raised for contract-related errors."""

    CONTRACT_ADDRESS_NOT_FOUND = "No contract address found for chain ID: {}"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ActorNotFoundError(RecallError):
    """Exception raised when an actor is not found."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Actor not found: {message}")


class BucketNotFoundError(RecallError):
    """Exception raised when a bucket is not found."""

    def __init__(self, bucket: str) -> None:
        super().__init__(f"Bucket not found: '{bucket}'")
        self.bucket = bucket


class ObjectNotFoundError(RecallError):
    """Exception raised when an object is not found."""

    def __init__(self, bucket: str, key: str) -> None:
        super().__init__(f"Object not found: no key '{key}' in bucket '{bucket}'")
        self.bucket = bucket
        self.key = key


class InvalidValueError(RecallError):
    """Exception raised for invalid parameter values."""

    FILE_NOT_FOUND = "File not found: {}"
    INVALID_RANGE = "Invalid range: {}"
    OBJECT_SIZE_EXCEEDS_LIMIT = "Object size ({}) exceeds maximum allowed size ({})"
    TTL_TOO_LOW = "TTL must be at least {} seconds"
    UNSUPPORTED_FILE_TYPE = "Unsupported file data type. Expected str, bytes, or file-like object."


class AddObjectError(RecallError):
    """Exception raised when adding an object fails."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Failed to add object: {message}")


class CreateBucketError(RecallError):
    """Exception raised when creating a bucket fails."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Failed to create bucket: {message}")


class UnexpectedError(RecallError):
    """Exception raised for unexpected errors."""

    BUCKET_CREATION_FAILED = "Failed to create bucket: no event logs found"
    UNKNOWN_CHAIN_ID = "Unknown chain ID: {}"
    UPLOAD_FAILED = "Failed to upload file: {}"
    DOWNLOAD_FAILED = "Failed to download object: {}"
    GET_OBJECT_FAILED = "Failed to get object: {}"
    ADD_OBJECT_FAILED = "Failed to add object: {}"
    DELETE_OBJECT_FAILED = "Failed to delete object: {}"
    GET_OBJECT_VALUE_FAILED = "Failed to get object value: {}"
    QUERY_BUCKET_FAILED = "Failed to query bucket: {}"
    PROCESS_FILE_DATA_FAILED = "Failed to process file data: {}"
    GET_NODE_INFO_FAILED = "Failed to get node info: {}"
    NETWORK_REQUEST_FAILED = "Error in network request: {}"


class UnhandledBucketError(RecallError):
    """Exception raised for unhandled bucket errors."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Bucket error: {message}")

class BlobNotFoundError(RecallError):
    """Exception raised when a blob is not found."""

    def __init__(self, blob_hash: str) -> None:
        super().__init__(f"Blob not found: '{blob_hash}'")
        self.blob_hash = blob_hash


class AddBlobError(RecallError):
    """Exception raised when adding a blob fails."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Failed to add blob: {message}")


class OverwriteBlobError(RecallError):
    """Exception raised when overwriting a blob fails."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Failed to overwrite blob: {message}")


class DeleteBlobError(RecallError):
    """Exception raised when deleting a blob fails."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Failed to delete blob: {message}")


class UnhandledBlobError(RecallError):
    """Exception raised for unhandled blob errors."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Blob error: {message}")
