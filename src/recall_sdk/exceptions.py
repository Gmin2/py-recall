"""Recall SDK exceptions."""


class RecallError(Exception):
    """Base exception for all Recall SDK errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ContractError(RecallError):
    """Exception raised for contract-related errors."""

    CONTRACT_ADDRESS_NOT_FOUND = "No contract address found for chain ID: {}"

    def _raise_bucket_creation_error():
        raise UnexpectedError(UnexpectedError.BUCKET_CREATION_FAILED)

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ObjectNotFoundError(RecallError):
    """Exception raised when an object is not found."""

    def __init__(self, bucket: str, key: str):
        super().__init__(f"Object not found: {bucket}/{key}")
        self.bucket = bucket
        self.key = key


class UnexpectedError(RecallError):
    """Exception raised for unexpected errors."""

    BUCKET_CREATION_FAILED = "Failed to create bucket: no event logs found"
    UNKNOWN_CHAIN_ID = "Unknown chain ID: {}"

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
