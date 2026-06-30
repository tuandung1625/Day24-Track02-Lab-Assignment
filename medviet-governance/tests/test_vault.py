import pytest
import os
import json
import pandas as pd
from src.encryption.vault import SimpleVault

@pytest.fixture
def vault(tmp_path):
    # Use a temporary file for the vault master key
    key_path = tmp_path / ".vault_key"
    return SimpleVault(master_key_path=str(key_path))

class TestEnvelopeEncryption:

    def test_roundtrip_encryption(self, vault):
        original_text = "Thong tin benh nhan nhay cam"
        
        # Encrypt
        encrypted_payload = vault.encrypt_data(original_text)
        assert "encrypted_dek" in encrypted_payload
        assert "ciphertext" in encrypted_payload
        assert encrypted_payload["algorithm"] == "AES-256-GCM"

        # Decrypt
        decrypted_text = vault.decrypt_data(encrypted_payload)
        assert decrypted_text == original_text

    def test_key_persistence(self, tmp_path):
        key_path = tmp_path / ".vault_key"
        
        # Instantiate first vault and encrypt
        vault1 = SimpleVault(master_key_path=str(key_path))
        encrypted = vault1.encrypt_data("Secret")

        # Instantiate second vault sharing the same key path
        vault2 = SimpleVault(master_key_path=str(key_path))
        decrypted = vault2.decrypt_data(encrypted)
        assert decrypted == "Secret"

    def test_column_encryption(self, vault):
        df = pd.DataFrame({
            "patient_id": [1, 2],
            "chuan_doan": ["Sot xuat huyet", "Viem phoi"]
        })
        
        # Encrypt column
        df_enc = vault.encrypt_column(df, "chuan_doan")
        
        # Assert column values are now JSON strings containing cipher payload
        for val in df_enc["chuan_doan"]:
            payload = json.loads(val)
            assert "encrypted_dek" in payload
            assert "ciphertext" in payload
            
            # Decrypt value
            decrypted = vault.decrypt_data(payload)
            assert decrypted in ["Sot xuat huyet", "Viem phoi"]
