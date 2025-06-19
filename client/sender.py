"""
Message sender client for secure messenger
"""

import asyncio
import argparse
import json
import urllib.request
import urllib.parse
from typing import Optional

from .crypto_utils import ClientCrypto


class MessageSender:
    """
    Client for sending encrypted messages
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize message sender
        
        Args:
            server_url: URL of the secure messenger server
        """
        self.server_url = server_url.rstrip('/')
        self.crypto = ClientCrypto()
    
    async def send_message(
        self,
        recipient_public_key: str,
        message: str,
        ttl: int = 3600
    ) -> Optional[dict]:
        """
        Send an encrypted message to a recipient
        
        Args:
            recipient_public_key: Recipient's public key as hex string
            message: Message to send
            ttl: Message time-to-live in seconds
            
        Returns:
            Server response or None if failed
        """
        try:
            # Encrypt the message for the recipient
            encrypted_data = self.crypto.encrypt_for_recipient(
                recipient_public_key, message
            )
            
            # Prepare request payload
            payload = {
                "token": encrypted_data["token"],
                "ciphertext": encrypted_data["ciphertext"],
                "nonce": encrypted_data["nonce"],
                "sender_public_key": encrypted_data["sender_public_key"],
                "ttl": ttl
            }
            
            # Send to server using urllib
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.server_url}/api/v1/send",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    return result
                else:
                    print(f"❌ Failed to send message: {response.status}")
                    print(f"Response: {response.read().decode('utf-8')}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None


async def main():
    """
    Command-line interface for sending messages
    """
    parser = argparse.ArgumentParser(description="Send encrypted messages")
    parser.add_argument(
        "--recipient-key",
        required=True,
        help="Recipient's public key (hex string)"
    )
    parser.add_argument(
        "--message",
        required=True,
        help="Message to send"
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=3600,
        help="Message TTL in seconds (default: 3600)"
    )
    
    args = parser.parse_args()
    
    print("🔐 Secure Messenger - Message Sender")
    print("=" * 40)
    
    # Initialize sender
    sender = MessageSender(args.server)
    
    print(f"📤 Sending message to: {args.recipient_key[:16]}...")
    print(f"💬 Message: {args.message}")
    print(f"⏰ TTL: {args.ttl} seconds")
    print()
    
    # Send the message
    result = await sender.send_message(
        args.recipient_key,
        args.message,
        args.ttl
    )
    
    if result:
        print("✅ Message sent successfully!")
        print(f"📧 Message ID: {result['message_id']}")
        print(f"🕐 Timestamp: {result['timestamp']}")
        print()
        print("🔒 The server cannot:")
        print("  • Read your message (it's encrypted)")
        print("  • Identify you (ephemeral key used)")  
        print("  • Identify the recipient (token is hashed)")
    else:
        print("❌ Failed to send message")


if __name__ == "__main__":
    asyncio.run(main()) 