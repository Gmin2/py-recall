"""Recall SDK exceptions."""


class RecallError(Exception):
    """Base exception for all Recall SDK errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ContractError(RecallError):
    """Exception raised for contract-related errors."""

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

class BucketNotFound(RecallError):
    """Exception raised when a bucket is not found"""
    
    def __init__(self, bucket: str):
        super().__init__(f"Bucket not found: '{bucket}'")
        self.bucket = bucket

class CreateBucketError(RecallError):
    """Exception raised when bucket creation fails"""
    
    def __init__(self, message: str):
        super().__init__(f"Failed to create bucket: {message}")

class AddObjectError(RecallError):
    """Exception raised when adding an object fails"""
    
    def __init__(self, message: str):
        super().__init__(f"Failed to add object: {message}")

class InvalidValue(RecallError):
    """Exception raised for invalid parameter values"""
    
    def __init__(self, message: str):
        super().__init__(message)
