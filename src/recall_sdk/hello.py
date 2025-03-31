print('hii')

# def _handle_bucket_creation_failure(self) -> None:
#         """Handle bucket creation failure by raising an appropriate error."""
#         raise UnexpectedError(UnexpectedError.BUCKET_CREATION_FAILED)

#     def create_bucket(self, owner: str | None = None, metadata: dict | None = None) -> CreatedBucketResponse | None:
#         """Create a bucket for a given owner or default to the signer's address"""
#         try:
#             # Function arguments
#             metadata = metadata or {}
#             metadata_list = [(key, str(value)) for key, value in metadata.items()]
#             owner = owner if owner is not None else self.get_signer_address()

#             # Build tx with custom gas params
#             gas = self.bucket_manager.functions.createBucket(
#                 owner,
#                 metadata_list,
#             ).estimate_gas()
#             tx = self.bucket_manager.functions.createBucket(
#                 owner,
#                 metadata_list,
#             ).build_transaction({
#                 "from": self.get_signer_address(),
#                 "gas": gas,
#                 "maxFeePerGas": currency.to_wei(100, "wei"),
#                 "maxPriorityFeePerGas": currency.to_wei(1, "wei"),
#                 "nonce": self.get_nonce(),
#             })
#             typed_tx = cast(dict[str, Any], tx)
#             # Sign and send the transaction
#             signed_tx = self.signer.sign_transaction(typed_tx)
#             tx_hash = self.w3.eth.send_raw_transaction(HexBytes(signed_tx["raw_transaction"]))

#             # Parse tx receipt
#             machine_facade_contract = self.w3.eth.contract(
#                 address=to_checksum_address(BUCKET_MANAGER_ADDRESS[self.get_chain_id()]), abi=IMACHINE_FACADE_ABI
#             )
#             rec = self.wait_for_tx_receipt(tx_hash)
#             log = self.parse_tx_receipt(machine_facade_contract, rec, "MachineInitialized")
#             args = log[0]["args"] if len(log) > 0 else None
#             if args is None:
#                 self._handle_bucket_creation_failure()
#             return CreatedBucketResponse(bucket=args["machineAddress"], kind=args["kind"])
#         except ContractLogicError as e:
#             raise ContractError(str(e)) from e
#         except Exception as e:
#             raise UnexpectedError(str(e)) from e

#     def list_buckets(self, owner: str | None = None) -> Any:
#         """List buckets for a given owner or default to the signer's address"""
#         try:
#             return self.bucket_manager.functions.listBuckets(
#                 owner if owner is not None else self.get_signer_address(),
#             ).call()
#         except ContractLogicError as e:
#             raise ContractError(str(e)) from e
#         except Exception as e:
#             raise UnexpectedError(str(e)) from e

#     def get_object_state(self, bucket: str, key: str) -> Any | None:
#         """Get an object's state (without downloading the object)"""
#         try:
#             bucket_addr = to_checksum_address(bucket)
#             return self.bucket_manager.functions.getObject(bucket_addr, key).call()
#         except ContractLogicError as e:
#             raise ContractError(str(e)) from e
#         except Exception as e:
#             raise UnexpectedError(str(e)) from e

#     def _ensure_object_exists(self, bucket: str, key: str, obj: dict | None) -> None:
#         """Helper function to check if object exists and raise if not."""
#         if obj is None:
#             raise ObjectNotFoundError(bucket, key)

#     def get_object(self, bucket: str, key: str) -> bytes:
#         """Get an object's data"""
#         try:
#             obj = self.get_object_state(bucket, key)
#             self._ensure_object_exists(bucket, key, obj)
#             response = requests.get(
#                 f"{self.object_api_url}/v1/objects/{bucket}/{key}",
#                 timeout=RPC_TIMEOUT,
#             )
#             if response.content:
#                 return response.content
#             else:
#                 return b""
#         except ContractLogicError as e:
#             raise ContractError(str(e)) from e
#         except Exception as e:
#             raise UnexpectedError(str(e)) from e