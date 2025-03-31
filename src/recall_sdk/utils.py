"""Utility functions for Recall SDK"""

from typing import Any, Dict, List

from web3 import Web3
from web3.contract import Contract
from web3.types import TxReceipt

def parse_event_from_transaction(
    contract: Contract, 
    receipt: TxReceipt, 
    event_name: str
) -> List[Dict]:
    """
    Parse events from a transaction receipt
    
    Args:
        contract: Contract instance
        receipt: Transaction receipt
        event_name: Name of the event to parse
        
    Returns:
        List of event logs matching the event name
    """
    logs = []
    
    for log in receipt.logs:
        try:
            parsed = contract.events[event_name]().process_receipt(receipt, [log.logIndex])
            if parsed:
                logs.extend(parsed)
        except Exception:
            continue
            
    return logs

def convertMetadataToAbiParams(metadata: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Convert metadata dictionary to ABI params format
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        List of key-value dictionaries
    """
    return [{"key": k, "value": v} for k, v in metadata.items()]

def convertAbiMetadataToObject(metadata: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Convert ABI metadata format to dictionary
    
    Args:
        metadata: List of key-value dictionaries
        
    Returns:
        Metadata dictionary
    """
    return {item["key"]: item["value"] for item in metadata}