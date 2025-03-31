import unittest
from unittest.mock import patch, MagicMock

from recall_sdk.client import Client, ContractOverrides
from recall_sdk.constants import (
    TESTNET_CHAIN_ID, 
    LOCALNET_CHAIN_ID,
    TESTNET_SUBNET_ID,
    TESTNET_BUCKET_MANAGER_ADDRESS,
    TESTNET_BLOB_MANAGER_ADDRESS,
    TESTNET_CREDIT_MANAGER_ADDRESS,
)
from recall_sdk.entities.ipc.subnet import SubnetId


class TestClient(unittest.TestCase):
    def setUp(self):
        # Mock web3 and other external dependencies
        self.web3_patcher = patch('recall_sdk.client.Web3')
        self.mock_web3 = self.web3_patcher.start()
        self.mock_w3 = MagicMock()
        self.mock_web3.return_value = self.mock_w3
        self.mock_w3.eth.chain_id = TESTNET_CHAIN_ID
        
        # Mock Account
        self.account_patcher = patch('recall_sdk.client.Account')
        self.mock_account = self.account_patcher.start()
        self.mock_signer = MagicMock()
        self.mock_account.from_key.return_value = self.mock_signer
        
        # Mock SubnetId
        self.subnet_id_patcher = patch('recall_sdk.client.SubnetId')
        self.mock_subnet_id = self.subnet_id_patcher.start()
        self.mock_subnet = MagicMock()
        self.mock_subnet.toString.return_value = TESTNET_SUBNET_ID
        self.mock_subnet_id.from_string.return_value = self.mock_subnet
        self.mock_subnet_id.from_chain.return_value = self.mock_subnet
        
        # Mock manager classes
        self.account_mgr_patcher = patch('recall_sdk.client.AccountManager')
        self.blob_mgr_patcher = patch('recall_sdk.client.BlobManager')
        self.bucket_mgr_patcher = patch('recall_sdk.client.BucketManager')
        self.credit_mgr_patcher = patch('recall_sdk.client.CreditManager')
        
        self.mock_account_mgr = self.account_mgr_patcher.start()
        self.mock_blob_mgr = self.blob_mgr_patcher.start()
        self.mock_bucket_mgr = self.bucket_mgr_patcher.start()
        self.mock_credit_mgr = self.credit_mgr_patcher.start()
        
        # Setup mock instances
        self.mock_account_mgr_instance = MagicMock()
        self.mock_blob_mgr_instance = MagicMock()
        self.mock_bucket_mgr_instance = MagicMock()
        self.mock_credit_mgr_instance = MagicMock()
        
        self.mock_account_mgr.return_value = self.mock_account_mgr_instance
        self.mock_blob_mgr.return_value = self.mock_blob_mgr_instance
        self.mock_bucket_mgr.return_value = self.mock_bucket_mgr_instance
        self.mock_credit_mgr.return_value = self.mock_credit_mgr_instance
    
    def tearDown(self):
        self.web3_patcher.stop()
        self.account_patcher.stop()
        self.subnet_id_patcher.stop()
        self.account_mgr_patcher.stop()
        self.blob_mgr_patcher.stop()
        self.bucket_mgr_patcher.stop()
        self.credit_mgr_patcher.stop()
    
    def test_client_with_empty_config(self):
        client = Client()
        self.assertEqual(client.chain_id, TESTNET_CHAIN_ID)
        
    def test_client_from_chain(self):
        client = Client.from_chain(LOCALNET_CHAIN_ID)
        self.assertEqual(client.chain_id, LOCALNET_CHAIN_ID)
        
    def test_client_from_chain_name(self):
        # Mock the chain map lookup
        client = Client.from_chain_name("localnet")
        self.assertEqual(client.chain_id, LOCALNET_CHAIN_ID)
        
    def test_client_with_private_key(self):
        private_key = "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
        client = Client(private_key=private_key)
        self.mock_account.from_key.assert_called_once_with(private_key)
        self.assertIsNotNone(client.signer)
        
    def test_get_subnet_id(self):
        client = Client()
        subnet_id = client.get_subnet_id()
        self.assertEqual(subnet_id, self.mock_subnet)
        
    def test_manager_creation(self):
        client = Client()
        
        # Test account manager creation
        account_mgr = client.account_manager()
        self.mock_account_mgr.assert_called_once_with(client)
        self.assertEqual(account_mgr, self.mock_account_mgr_instance)
        
        # Test blob manager creation
        blob_mgr = client.blob_manager()
        self.mock_blob_mgr.assert_called_once_with(client, None)
        self.assertEqual(blob_mgr, self.mock_blob_mgr_instance)
        
        # Test bucket manager creation
        bucket_mgr = client.bucket_manager()
        self.mock_bucket_mgr.assert_called_once_with(client, None)
        self.assertEqual(bucket_mgr, self.mock_bucket_mgr_instance)
        
        # Test credit manager creation
        credit_mgr = client.credit_manager()
        self.mock_credit_mgr.assert_called_once_with(client, None)
        self.assertEqual(credit_mgr, self.mock_credit_mgr_instance)
    
    def test_contract_overrides(self):
        # Setup contract overrides
        test_address = "0xB5B359EEc9549b0D65B3D1137EFDf51f09c65c5b"
        overrides = ContractOverrides(
            bucket_manager={TESTNET_CHAIN_ID: test_address},
            blob_manager={TESTNET_CHAIN_ID: test_address},
            credit_manager={TESTNET_CHAIN_ID: test_address},
            account_manager={
                "gateway_manager": {TESTNET_CHAIN_ID: test_address},
                "recall_erc20": {TESTNET_CHAIN_ID: test_address},
            }
        )
        
        client = Client(contract_overrides=overrides)
        
        # Test that managers use the overridden addresses
        client.bucket_manager()
        self.mock_bucket_mgr.assert_called_with(client, test_address)
        
        client.blob_manager()
        self.mock_blob_mgr.assert_called_with(client, test_address)
        
        client.credit_manager()
        self.mock_credit_mgr.assert_called_with(client, test_address)
        
        # Manager methods should pass overrides to internal components
        # This would need more mocking to test completely, similar to the JS version


if __name__ == '__main__':
    unittest.main()