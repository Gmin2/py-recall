"""
Credit manager to handle credit operations on the Recall Network.
"""

from typing import Any, Dict, List, Optional

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.exceptions import ContractLogicError

from ..constants import CREDIT_MANAGER_ABI, CREDIT_MANAGER_ADDRESS
from ..exceptions import (
    ActorNotFoundError,
    ContractError,
    InvalidValueError,
    UnexpectedError,
)
from ..types import (
    CreditAccountResult,
    CreditApprovalsResult,
    CreditBalanceResult,
    CreditStatsResult,
    ResponseWithResult,
    TransactionResponse,
)
from .base_manager import BaseManager


class CreditManager(BaseManager):
    """
    Manager for credit operations on the Recall Network

    Provides methods to buy, approve, revoke credits, and check balances.
    """

    def __init__(self, client: Any, contract_address: Optional[str] = None) -> None:
        """
        Initialize the CreditManager

        Args:
            client: The Recall client instance
            contract_address: Optional override for the contract address
        """
        super().__init__(client, contract_address)
        self.contract = self.get_contract(CREDIT_MANAGER_ABI, CREDIT_MANAGER_ADDRESS)

    def approve(
        self,
        to: ChecksumAddress,
        caller: Optional[List[ChecksumAddress]] = None,
        credit_limit: int = 0,
        gas_fee_limit: int = 0,
        ttl: int = 0,
        from_address: Optional[ChecksumAddress] = None,
    ) -> TransactionResponse:
        """
        Approve credit spending for another address

        Args:
            to: Address to approve credits for
            caller: Optional list of allowed caller addresses
            credit_limit: Maximum amount of credits that can be used
            gas_fee_limit: Maximum amount of gas fees
            ttl: Time-to-live for the approval in seconds
            from_address: Address approving the credits (defaults to signer)

        Returns:
            TransactionResponse: Transaction receipt information

        Raises:
            InvalidValueError: If the from_address doesn't match the signer
            ActorNotFoundError: If the actor is not found
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Default values
            caller = caller or []
            if from_address is None:
                from_address = self.client.signer.address

            from_addr = Web3.to_checksum_address(from_address)
            to_addr = Web3.to_checksum_address(to)
            caller_addrs = [Web3.to_checksum_address(addr) for addr in caller]

            # Get contract gas estimate
            gas = self.contract.functions.approveCredit(
                from_addr,
                to_addr,
                caller_addrs,
                credit_limit,
                gas_fee_limit,
                ttl,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.approveCredit(
                from_addr,
                to_addr,
                caller_addrs,
                credit_limit,
                gas_fee_limit,
                ttl,
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
            if "does not match origin or caller" in error_msg:
                raise InvalidValueError(
                    f"'from' address '{from_address}' does not match origin or caller '{self.client.signer.address}'"
                ) from e
            if "actor not found" in error_msg or "actor::resolve_address" in error_msg:
                raise ActorNotFoundError(str(e)) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to approve credits: {e!s}") from e

    def buy(self, amount: int, recipient: Optional[ChecksumAddress] = None) -> TransactionResponse:
        """
        Buy credits by sending RECALL tokens

        Args:
            amount: Amount of RECALL tokens to send
            recipient: Optional recipient address (defaults to signer)

        Returns:
            TransactionResponse: Transaction receipt information

        Raises:
            InvalidValueError: If the signer has insufficient funds
            ActorNotFoundError: If the actor is not found
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Check balance
            balance = self.w3.eth.get_balance(self.client.signer.address)
            if balance < amount:
                raise InvalidValueError(f"Insufficient funds: balance {balance} less than amount {amount}")

            # Default recipient to signer address if not provided
            recipient_addr = self.client.signer.address
            if recipient:
                recipient_addr = Web3.to_checksum_address(recipient)

            # Get contract gas estimate and function to call
            if recipient:
                gas = self.contract.functions.buyCredit(recipient_addr).estimate_gas({
                    "from": self.client.signer.address,
                    "value": amount,
                })
                function_call = self.contract.functions.buyCredit(recipient_addr)
            else:
                gas = self.contract.functions.buyCredit().estimate_gas({
                    "from": self.client.signer.address,
                    "value": amount,
                })
                function_call = self.contract.functions.buyCredit()

            # Build transaction
            tx = function_call.build_transaction({
                "from": self.client.signer.address,
                "value": amount,
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
            if "insufficient funds" in error_msg:
                raise InvalidValueError(f"Insufficient funds: {e!s}") from e
            if "actor not found" in error_msg or "actor::resolve_address" in error_msg:
                raise ActorNotFoundError(str(e)) from e
            raise ContractError(str(e)) from e
        except InvalidValueError:
            # Re-raise InvalidValueError
            raise
        except Exception as e:
            raise UnexpectedError(f"Failed to buy credits: {e!s}") from e

    def revoke(
        self,
        to: ChecksumAddress,
        required_caller: Optional[ChecksumAddress] = None,
        from_address: Optional[ChecksumAddress] = None,
    ) -> TransactionResponse:
        """
        Revoke credit approval

        Args:
            to: Address to revoke credits from
            required_caller: Address of required caller (defaults to 'to')
            from_address: Address revoking the credits (defaults to signer)

        Returns:
            TransactionResponse: Transaction receipt information

        Raises:
            InvalidValueError: If the from_address doesn't match the signer
            ActorNotFoundError: If the actor is not found
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Default values
            if from_address is None:
                from_address = self.client.signer.address

            if required_caller is None:
                required_caller = to

            from_addr = Web3.to_checksum_address(from_address)
            to_addr = Web3.to_checksum_address(to)
            caller_addr = Web3.to_checksum_address(required_caller)

            # Get contract gas estimate
            gas = self.contract.functions.revokeCredit(
                from_addr,
                to_addr,
                caller_addr,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.revokeCredit(
                from_addr,
                to_addr,
                caller_addr,
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
            if "does not match origin or caller" in error_msg:
                raise InvalidValueError(
                    f"'from' address '{from_address}' does not match origin or caller '{self.client.signer.address}'"
                ) from e
            if "actor not found" in error_msg or "actor::resolve_address" in error_msg:
                raise ActorNotFoundError(str(e)) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to revoke credits: {e!s}") from e

    def set_account_sponsor(
        self, sponsor: ChecksumAddress, from_address: Optional[ChecksumAddress] = None
    ) -> TransactionResponse:
        """
        Set account sponsor

        Args:
            sponsor: Address of the sponsor
            from_address: Address to set sponsor for (defaults to signer)

        Returns:
            TransactionResponse: Transaction receipt information

        Raises:
            ActorNotFoundError: If the actor is not found
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Default from_address to signer address
            if from_address is None:
                from_address = self.client.signer.address

            from_addr = Web3.to_checksum_address(from_address)
            sponsor_addr = Web3.to_checksum_address(sponsor)

            # Get contract gas estimate
            gas = self.contract.functions.setAccountSponsor(
                from_addr,
                sponsor_addr,
            ).estimate_gas({"from": self.client.signer.address})

            # Build transaction
            tx = self.contract.functions.setAccountSponsor(
                from_addr,
                sponsor_addr,
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
            if "actor not found" in str(e).lower() or "actor::resolve_address" in str(e).lower():
                raise ActorNotFoundError(str(e)) from e
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to set account sponsor: {e!s}") from e

    def get_account(
        self, address: Optional[ChecksumAddress] = None, block_number: Optional[int] = None
    ) -> ResponseWithResult[CreditAccountResult]:
        """
        Get account details including approvals

        Args:
            address: Address to get account for (defaults to signer)
            block_number: Optional block number to query at

        Returns:
            ResponseWithResult[CreditAccountResult]: Account details including approvals

        Raises:
            InvalidValueError: If no address is provided and no wallet is connected
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Default to signer address
            if address is None:
                address = self.client.signer.address

            if not address:
                raise InvalidValueError("Must provide an address or connect a wallet client")

            addr = Web3.to_checksum_address(address)

            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            # Call contract to get account
            account = self.contract.functions.getAccount(addr).call(**call_params)

            # Transform the nested tuples into a more usable dictionary structure
            result = {
                "capacityUsed": account[0],
                "creditFree": account[1],
                "creditCommitted": account[2],
                "creditSponsor": account[3],
                "lastDebitEpoch": account[4],
                "approvalsTo": self._transform_approvals(account[5]),
                "approvalsFrom": self._transform_approvals(account[6]),
                "maxTtl": account[7],
                "gasAllowance": account[8],
            }

            return {"result": result}

        except ContractLogicError as e:
            if "actor not found" in str(e).lower() or "actor::resolve_address" in str(e).lower():
                # Return empty account if actor not found, mimicking JS SDK behavior
                empty_account = {
                    "capacityUsed": 0,
                    "creditFree": 0,
                    "creditCommitted": 0,
                    "creditSponsor": "0x0000000000000000000000000000000000000000",
                    "lastDebitEpoch": 0,
                    "approvalsTo": [],
                    "approvalsFrom": [],
                    "maxTtl": 0,
                    "gasAllowance": 0,
                }
                return {"result": empty_account}
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get account details: {e!s}") from e

    def get_credit_approvals(
        self,
        address: Optional[ChecksumAddress] = None,
        filter_from: Optional[ChecksumAddress] = None,
        filter_to: Optional[ChecksumAddress] = None,
        block_number: Optional[int] = None,
    ) -> ResponseWithResult[CreditApprovalsResult]:
        """
        Get credit approvals with optional filtering

        Args:
            address: Address to get approvals for (defaults to signer)
            filter_from: Filter by from address
            filter_to: Filter by to address
            block_number: Optional block number to query at

        Returns:
            ResponseWithResult[CreditApprovalsResult]: Filtered credit approvals

        Raises:
            InvalidValueError: If no address is provided and no wallet is connected
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        # Get account details
        account_response = self.get_account(address, block_number)
        account = account_response["result"]

        # Apply filters
        approvals_to = account["approvalsTo"]
        approvals_from = account["approvalsFrom"]

        # Filter by to address if provided
        if filter_to:
            filter_to_addr = Web3.to_checksum_address(filter_to)
            approvals_to = [approval for approval in approvals_to if approval["addr"] == filter_to_addr]

        # Filter by from address if provided
        if filter_from:
            filter_from_addr = Web3.to_checksum_address(filter_from)
            approvals_from = [approval for approval in approvals_from if approval["addr"] == filter_from_addr]

        return {"result": {"approvalsTo": approvals_to, "approvalsFrom": approvals_from}}

    def get_credit_balance(
        self, address: Optional[ChecksumAddress] = None, block_number: Optional[int] = None
    ) -> ResponseWithResult[CreditBalanceResult]:
        """
        Get credit balance

        Args:
            address: Address to get balance for (defaults to signer)
            block_number: Optional block number to query at

        Returns:
            ResponseWithResult[CreditBalanceResult]: Credit balance information

        Raises:
            InvalidValueError: If no address is provided and no wallet is connected
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Default to signer address
            if address is None:
                address = self.client.signer.address

            if not address:
                raise InvalidValueError("Must provide an address or connect a wallet client")

            addr = Web3.to_checksum_address(address)

            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            # Call contract to get credit balance
            balance = self.contract.functions.getCreditBalance(addr).call(**call_params)

            # Transform the nested tuples into a more usable dictionary structure
            result = {
                "creditFree": balance[0],
                "creditCommitted": balance[1],
                "creditSponsor": balance[2],
                "lastDebitEpoch": balance[3],
                "approvalsTo": self._transform_approvals(balance[4]),
                "approvalsFrom": self._transform_approvals(balance[5]),
                "gasAllowance": balance[6],
            }

            return {"result": result}

        except ContractLogicError as e:
            if "actor not found" in str(e).lower() or "actor::resolve_address" in str(e).lower():
                # Return empty balance if actor not found, mimicking JS SDK behavior
                empty_balance = {
                    "creditFree": 0,
                    "creditCommitted": 0,
                    "creditSponsor": "0x0000000000000000000000000000000000000000",
                    "lastDebitEpoch": 0,
                    "approvalsTo": [],
                    "approvalsFrom": [],
                    "gasAllowance": 0,
                }
                return {"result": empty_balance}
            raise ContractError(str(e)) from e
        except InvalidValueError:
            # Re-raise InvalidValueError
            raise
        except Exception as e:
            raise UnexpectedError(f"Failed to get credit balance: {e!s}") from e

    def get_credit_stats(self, block_number: Optional[int] = None) -> ResponseWithResult[CreditStatsResult]:
        """
        Get credit stats for the subnet

        Args:
            block_number: Optional block number to query at

        Returns:
            ResponseWithResult[CreditStatsResult]: Credit stats information

        Raises:
            ContractError: If the contract interaction fails
            UnexpectedError: For unexpected errors
        """
        try:
            # Add block number to call if provided
            call_params = {}
            if block_number is not None:
                call_params["block_identifier"] = block_number

            # Call contract to get credit stats
            stats = self.contract.functions.getCreditStats().call(**call_params)

            # Transform the result into a more usable dictionary structure
            result = {
                "balance": stats[0],
                "creditSold": stats[1],
                "creditCommitted": stats[2],
                "creditDebited": stats[3],
                "tokenCreditRate": stats[4],
                "numAccounts": stats[5],
            }

            return {"result": result}

        except ContractLogicError as e:
            raise ContractError(str(e)) from e
        except Exception as e:
            raise UnexpectedError(f"Failed to get credit stats: {e!s}") from e

    def format_credit_stats(self, stats: CreditStatsResult) -> Dict[str, str]:
        """
        Format credit stats to match CLI output

        Args:
            stats: Raw credit stats from contract

        Returns:
            Dict[str, str]: Formatted stats with decimals
        """
        # Format large numbers to show with proper decimals
        return {
            "balance": self._format_number(stats["balance"]),
            "credit_sold": self._format_number(stats["creditSold"]),
            "credit_committed": self._format_number(stats["creditCommitted"]),
            "credit_debited": self._format_number(stats["creditDebited"]),
            "token_credit_rate": str(stats["tokenCreditRate"]),
            "num_accounts": stats["numAccounts"],
        }

    def _format_number(self, value: int) -> str:
        """Format large numbers to match CLI output with 18 decimals."""
        if value == 0:
            return "0.0"

        # Convert to string with 18 decimal places
        value_str = str(value)
        if len(value_str) <= 18:
            # Less than 1
            return "0." + value_str.zfill(18)[-18:]
        else:
            # Greater than 1
            decimal_pos = len(value_str) - 18
            return value_str[:decimal_pos] + "." + value_str[decimal_pos:]

    def _transform_approvals(self, approvals: List[tuple]) -> List[Dict[str, Any]]:
        """
        Transform approval tuples from contract into dictionaries

        Args:
            approvals: List of approval tuples from contract

        Returns:
            List[Dict[str, Any]]: Transformed approvals
        """
        result = []
        for approval in approvals:
            addr = approval[0]
            approval_data = approval[1]

            transformed = {
                "addr": addr,
                "approval": {
                    "creditLimit": approval_data[0],
                    "gasFeeLimit": approval_data[1],
                    "expiry": approval_data[2],
                    "creditUsed": approval_data[3],
                    "gasFeeUsed": approval_data[4],
                },
            }
            result.append(transformed)

        return result
