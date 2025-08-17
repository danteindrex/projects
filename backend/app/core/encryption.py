from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class EncryptionService:
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.cipher_suite = Fernet(self.master_key)
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create the master encryption key"""
        # In production, this should be stored securely (e.g., AWS KMS, Azure Key Vault)
        if hasattr(settings, 'MASTER_ENCRYPTION_KEY') and settings.MASTER_ENCRYPTION_KEY:
            return base64.urlsafe_b64decode(settings.MASTER_ENCRYPTION_KEY)
        
        # For development, generate a key
        if settings.ENVIRONMENT == "development":
            key = Fernet.generate_key()
            logger.warning("Generated new encryption key for development. Store this securely in production!")
            return key
        
        raise ValueError("MASTER_ENCRYPTION_KEY must be set in production")
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a base64 encoded encrypted string"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_credentials(self, credentials: dict) -> str:
        """Encrypt a credentials dictionary"""
        import json
        try:
            credentials_json = json.dumps(credentials)
            return self.encrypt(credentials_json)
        except Exception as e:
            logger.error(f"Credentials encryption failed: {e}")
            raise
    
    def decrypt_credentials(self, encrypted_credentials: str) -> dict:
        """Decrypt credentials back to a dictionary"""
        import json
        try:
            decrypted_json = self.decrypt(encrypted_credentials)
            return json.loads(decrypted_json)
        except Exception as e:
            logger.error(f"Credentials decryption failed: {e}")
            raise
    
    def generate_key_id(self) -> str:
        """Generate a unique key ID for tracking encryption keys"""
        return base64.urlsafe_b64encode(os.urandom(16)).decode()
    
    def rotate_keys(self) -> str:
        """Rotate encryption keys (for security)"""
        new_key = Fernet.generate_key()
        new_cipher_suite = Fernet(new_key)
        
        # Store the new key securely
        # In production, this should update the master key in your secure storage
        
        self.master_key = new_key
        self.cipher_suite = new_cipher_suite
        
        return base64.urlsafe_b64encode(new_key).decode()

# Global encryption service instance
encryption_service = EncryptionService()

def encrypt_data(data: str) -> str:
    """Convenience function to encrypt data"""
    return encryption_service.encrypt(data)

def decrypt_data(encrypted_data: str) -> str:
    """Convenience function to decrypt data"""
    return encryption_service.decrypt(encrypted_data)

def encrypt_credentials(credentials: dict) -> str:
    """Convenience function to encrypt credentials"""
    return encryption_service.encrypt_credentials(credentials)

def decrypt_credentials(encrypted_credentials: str) -> dict:
    """Convenience function to decrypt credentials"""
    return encryption_service.decrypt_credentials(encrypted_credentials)
