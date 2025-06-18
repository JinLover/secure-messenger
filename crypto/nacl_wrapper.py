"""
PyNaCl wrapper for secure messaging
Provides high-level cryptographic functions for the secure messenger
"""

import hashlib
import secrets
from typing import Tuple, Dict, Any
from nacl.public import PrivateKey, PublicKey, Box
from nacl.utils import random
from nacl.encoding import HexEncoder


def generate_keypair() -> Tuple[str, str]:
    """
    Generate a new keypair for a user
    
    Returns:
        Tuple[str, str]: (private_key_hex, public_key_hex)
    """
    private_key = PrivateKey.generate()
    public_key = private_key.public_key
    
    # Convert to hex strings
    private_key_hex = bytes(private_key).hex()
    public_key_hex = bytes(public_key).hex()
    
    return (private_key_hex, public_key_hex)


def encrypt_message(recipient_public_key_hex: str, plaintext: str) -> Dict[str, Any]:
    """
    Encrypt a message for a specific recipient
    
    Args:
        recipient_public_key_hex: Recipient's public key as hex string
        plaintext: Message to encrypt
        
    Returns:
        Dict containing encrypted message components
    """
    try:
        # Generate ephemeral keypair for this message (Perfect Forward Secrecy)
        sender_private_key = PrivateKey.generate()
        sender_public_key = sender_private_key.public_key
        
        # Decode recipient's public key
        recipient_public_key_bytes = bytes.fromhex(recipient_public_key_hex)
        recipient_public_key = PublicKey(recipient_public_key_bytes)
        
        # Create box for encryption
        box = Box(sender_private_key, recipient_public_key)
        
        # Ensure plaintext is properly encoded to bytes
        if isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode('utf-8')
        else:
            plaintext_bytes = plaintext
        
        # Encrypt the message
        encrypted = box.encrypt(plaintext_bytes)
        
        # Generate routing token (hash of recipient's public key)
        token = generate_token(recipient_public_key_hex)
        
        # Convert sender public key to hex
        sender_public_key_hex = bytes(sender_public_key).hex()
        
        return {
            "token": token,
            "ciphertext": encrypted.ciphertext.hex(),
            "nonce": encrypted.nonce.hex(),
            "sender_public_key": sender_public_key_hex,
            "timestamp": None  # Server will add timestamp
        }
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")


def decrypt_message(
    recipient_private_key_hex: str,
    sender_public_key_hex: str,
    nonce_hex: str,
    ciphertext_hex: str
) -> str:
    """
    Decrypt a message using recipient's private key
    
    Args:
        recipient_private_key_hex: Recipient's private key as hex string
        sender_public_key_hex: Sender's public key as hex string
        nonce_hex: Nonce used for encryption as hex string
        ciphertext_hex: Encrypted message as hex string
        
    Returns:
        Decrypted plaintext message
    """
    try:
        # Decode keys from hex
        recipient_private_key_bytes = bytes.fromhex(recipient_private_key_hex)
        recipient_private_key = PrivateKey(recipient_private_key_bytes)
        
        sender_public_key_bytes = bytes.fromhex(sender_public_key_hex)
        sender_public_key = PublicKey(sender_public_key_bytes)
        
        # Create box for decryption
        box = Box(recipient_private_key, sender_public_key)
        
        # Decode encrypted components
        nonce = bytes.fromhex(nonce_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)
        
        # Decrypt the message
        decrypted = box.decrypt(ciphertext, nonce)
        
        return decrypted.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


def generate_token(public_key_hex: str) -> str:
    """
    Generate a routing token from public key
    Uses SHA-256 hash to create a token that can't be reverse engineered
    
    Args:
        public_key_hex: Public key as hex string
        
    Returns:
        Token as hex string
    """
    # Add salt to prevent rainbow table attacks
    salt = b"secure_messenger_routing_salt_v1"
    
    # Create hash
    hasher = hashlib.sha256()
    hasher.update(salt)
    hasher.update(bytes.fromhex(public_key_hex))
    
    return hasher.hexdigest()


def verify_token(public_key_hex: str, token: str) -> bool:
    """
    Verify that a token was generated from a specific public key
    
    Args:
        public_key_hex: Public key as hex string
        token: Token to verify
        
    Returns:
        True if token is valid for the public key
    """
    expected_token = generate_token(public_key_hex)
    
    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(expected_token, token)


def generate_message_id() -> str:
    """
    Generate a unique message ID
    
    Returns:
        Unique message ID as hex string
    """
    return secrets.token_hex(16) 