"""Type definitions for the Recall SDK."""

from dataclasses import dataclass
from typing import Any, TypedDict, Union

from eth_typing import ChecksumAddress


class CreateBucketResponse(TypedDict):
    """Type definition for BucketCreated event data."""

    kind: int
    bucket: ChecksumAddress


class MachineInitializedEvent(TypedDict):
    """Type definition for MachineInitialized event data."""

    kind: int
    machineAddress: ChecksumAddress


@dataclass
class BucketMetadata:
    """Bucket metadata class."""

    kind: int
    addr: ChecksumAddress
    metadata: dict[str, str]


@dataclass
class ObjectValue:
    """Object value class for metadata."""

    blobHash: str
    recoveryHash: str
    size: int
    expiry: int
    metadata: dict[str, str]


@dataclass
class ObjectState:
    """Object state for query results."""

    blobHash: str
    size: int
    expiry: int
    metadata: dict[str, str]


@dataclass
class QueryObject:
    """Single object in a query result."""

    key: str
    state: ObjectState


@dataclass
class QueryResult:
    """Query result class."""

    objects: list[dict[str, Any]]
    commonPrefixes: list[str]
    nextKey: str


class EventLog(TypedDict):
    """Type definition for processed event logs."""

    args: Union[MachineInitializedEvent]  # Can extend with other event types as needed
    event: str
    logIndex: int
    transactionIndex: int
    transactionHash: str
    address: str
    blockHash: str
    blockNumber: int
