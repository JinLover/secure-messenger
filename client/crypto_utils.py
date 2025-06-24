"""
Client-side cryptographic utilities
"""

import json
import os
from pathlib import Path
from typing import Tuple, Optional
from crypto.nacl_wrapper import (
    generate_keypair,
    encrypt_message,
    decrypt_message,
    generate_token
)


class ClientCrypto:
    """
    Client-side cryptographic operations
    Handles key management and message encryption/decryption
    """
    
    def __init__(self, keys_dir: str = "keys"):
        """
        Initialize client crypto with keys directory
        
        Args:
            keys_dir: Directory to store keys
        """
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(exist_ok=True)
        
        self.private_key: Optional[str] = None
        self.public_key: Optional[str] = None
        self.token: Optional[str] = None
    
    def generate_new_keypair(self, save_to_file: bool = True) -> Tuple[str, str]:
        """
        Generate a new keypair
        
        Args:
            save_to_file: Whether to save keys to file
            
        Returns:
            Tuple of (private_key_hex, public_key_hex)
        """
        private_key, public_key = generate_keypair()
        
        self.private_key = private_key
        self.public_key = public_key
        self.token = generate_token(public_key)
        
        if save_to_file:
            self.save_keys()
        
        return private_key, public_key
    
    def load_keys(self, filename: str = "keys.json") -> bool:
        """
        Load keys from file
        
        Args:
            filename: Name of the keys file
            
        Returns:
            True if keys were loaded successfully
        """
        keys_file = self.keys_dir / filename
        
        if not keys_file.exists():
            return False
        
        try:
            with open(keys_file, 'r') as f:
                keys_data = json.load(f)
            
            self.private_key = keys_data["private_key"]
            self.public_key = keys_data["public_key"]
            self.token = keys_data["token"]
            
            return True
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return False
    
    def save_keys(self, filename: str = "keys.json") -> bool:
        """
        Save keys to file
        
        Args:
            filename: Name of the keys file
            
        Returns:
            True if keys were saved successfully
        """
        if not self.private_key or not self.public_key:
            return False
        
        keys_file = self.keys_dir / filename
        
        keys_data = {
            "private_key": self.private_key,
            "public_key": self.public_key,
            "token": self.token
        }
        
        try:
            with open(keys_file, 'w') as f:
                json.dump(keys_data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(keys_file, 0o600)
            
            return True
        except Exception:
            return False
    
    def encrypt_for_recipient(self, recipient_public_key: str, message: str) -> dict:
        """
        Encrypt a message for a specific recipient
        
        Args:
            recipient_public_key: Recipient's public key as hex string
            message: Message to encrypt
            
        Returns:
            Dictionary with encrypted message components
        """
        return encrypt_message(recipient_public_key, message)
    
    def decrypt_message_for_me(
        self,
        sender_public_key: str,
        nonce: str,
        ciphertext: str
    ) -> str:
        """
        Decrypt a message sent to this client
        
        Args:
            sender_public_key: Sender's public key as hex string
            nonce: Nonce used for encryption as hex string
            ciphertext: Encrypted message as hex string
            
        Returns:
            Decrypted message
        """
        if not self.private_key:
            raise ValueError("No private key loaded")
        
        return decrypt_message(
            self.private_key,
            sender_public_key,
            nonce,
            ciphertext
        )
    
    def get_public_key(self) -> Optional[str]:
        """Get the public key"""
        return self.public_key
    
    def get_token(self) -> Optional[str]:
        """Get the routing token"""
        return self.token
    
    def export_public_key(self, filename: str = "public_key.txt") -> bool:
        """
        Export public key to a file for sharing
        
        Args:
            filename: Name of the file to export to
            
        Returns:
            True if export was successful
        """
        if not self.public_key:
            return False
        
        export_file = self.keys_dir / filename
        
        try:
            with open(export_file, 'w') as f:
                f.write(self.public_key)
            
            return True
        except Exception:
            return False
    
    def import_public_key(self, filename: str) -> Optional[str]:
        """
        Import a public key from a file
        
        Args:
            filename: Name of the file to import from
            
        Returns:
            The imported public key, or None if failed
        """
        try:
            with open(filename, 'r') as f:
                public_key = f.read().strip()
            
            # Basic validation - check if it looks like a hex string
            if len(public_key) == 64 and all(c in '0123456789abcdefABCDEF' for c in public_key):
                return public_key
            
            return None
        except Exception:
            return None 