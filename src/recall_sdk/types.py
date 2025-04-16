"""Type definitions for the Recall SDK."""

from dataclasses import dataclass
from typing import Any, Generic, TypedDict, TypeVar, Union

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


@dataclass
class CreditApproval:
    """Credit approval details."""

    creditLimit: int
    gasFeeLimit: int
    expiry: int
    creditUsed: int
    gasFeeUsed: int


@dataclass
class Approval:
    """Approval with address and approval details."""

    addr: ChecksumAddress
    approval: CreditApproval


class CreditAccountResult(TypedDict):
    """Type definition for account details response."""

    capacityUsed: int
    creditFree: int
    creditCommitted: int
    creditSponsor: ChecksumAddress
    lastDebitEpoch: int
    approvalsTo: list[Approval]
    approvalsFrom: list[Approval]
    maxTtl: int
    gasAllowance: int


class CreditBalanceResult(TypedDict):
    """Type definition for credit balance response."""

    creditFree: int
    creditCommitted: int
    creditSponsor: ChecksumAddress
    lastDebitEpoch: int
    approvalsTo: list[Approval]
    approvalsFrom: list[Approval]
    gasAllowance: int


class CreditApprovalsResult(TypedDict):
    """Type definition for credit approvals response."""

    approvalsTo: list[Approval]
    approvalsFrom: list[Approval]


class CreditStatsResult(TypedDict):
    """Type definition for credit stats response."""

    balance: int
    creditSold: int
    creditCommitted: int
    creditDebited: int
    tokenCreditRate: int
    numAccounts: int


T = TypeVar("T")


class ResponseWithResult(TypedDict, Generic[T]):
    """Generic type for responses with a result."""

    result: T


class TransactionResponse(TypedDict):
    """Type definition for transaction responses."""

    receipt: dict[str, Any]
    transactionHash: str
