from typing import Any, Optional, cast

from eth_utils import currency, to_checksum_address
from web3.exceptions import ContractLogicError
from web3.types import HexBytes

from ..constants import BUCKET_MANAGER_ABI, BUCKET_MANAGER_ADDRESS, IMACHINE_FACADE_ABI
from ..exceptions import ContractError, ObjectNotFoundError, UnexpectedError, _raise_bucket_creation_error
from ..types import CreatedBucketResponse
from .base_manager import BaseManager


class BucketManager(BaseManager):
    """Manager for bucket operations"""

    def __init__(self, client, contract_address=None):
        super().__init__(client, contract_address)
        self.contract = self.get_contract(BUCKET_MANAGER_ABI, BUCKET_MANAGER_ADDRESS)

    def create(self, owner: Optional[str] = None, metadata: Optional[dict[str, str]] = None) -> CreatedBucketResponse:
        """Create a bucket for a given owner or default to the signer's address"""
        try:
            # Function arguments
            metadata = metadata or {}
            metadata_list = [(key, str(value)) for key, value in metadata.items()]
            owner = owner if owner is not None else self.client.get_signer_address()

            # Build tx with custom gas params
            gas = self.contract.functions.createBucket(
                owner,
                metadata_list,
            ).estimate_gas()

            tx = self.contract.functions.createBucket(
                owner,
                metadata_list,
            ).build_transaction({
                "from": self.client.get_signer_address(),
                "gas": gas,
                "maxFeePerGas": currency.to_wei(100, "wei"),
                "maxPriorityFeePerGas": currency.to_wei(1, "wei"),
                "nonce": self.client.get_nonce(),
            })

            typed_tx = cast(dict[str, Any], tx)

            # Sign and send the transaction
            signed_tx = self.client.signer.sign_transaction(typed_tx)
            tx_hash = self.w3.eth.send_raw_transaction(HexBytes(signed_tx["raw_transaction"]))

            # Parse tx receipt
            machine_facade_contract = self.w3.eth.contract(
                address=to_checksum_address(BUCKET_MANAGER_ADDRESS[self.w3.eth.chain_id]), abi=IMACHINE_FACADE_ABI
            )

            rec = self.client.wait_for_tx_receipt(tx_hash)
            log = self.client.parse_tx_receipt(machine_facade_contract, rec, "MachineInitialized")
            args = log[0]["args"] if len(log) > 0 else None

            if args is None:
                _raise_bucket_creation_error()

            return CreatedBucketResponse(bucket=args["machineAddress"], kind=args["kind"])

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(str(e)) from e

    def list(self, owner: Optional[str] = None) -> list[Any]:
        """List buckets for a given owner or default to the signer's address"""

        try:
            return self.contract.functions.listBuckets(
                owner if owner is not None else self.client.get_signer_address(),
            ).call()
        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(str(e)) from e

    def get_object_state(self, bucket: str, key: str) -> Any:
        """Get an object's state (without downloading the object)"""
        try:
            bucket_addr = to_checksum_address(bucket)
            return self.contract.functions.getObject(bucket_addr, key).call()
        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(str(e)) from e

    def get_object(self, bucket: str, key: str) -> bytes:
        """Get an object's data"""
        import requests

        from ..constants import RPC_TIMEOUT

        def _raise_object_not_found(bucket: str, key: str):
            raise ObjectNotFoundError(bucket, key)

        try:
            obj = self.get_object_state(bucket, key)
            if obj is None:
                _raise_object_not_found(bucket, key)
            response = requests.get(
                f"{self.client.object_api_url}/v1/objects/{bucket}/{key}",
                timeout=RPC_TIMEOUT,
            )

            if response.content:
                return response.content
            else:
                return b""

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(str(e)) from e
