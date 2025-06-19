"""
Message receiver client for secure messenger
"""

import asyncio
import argparse
import time
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Optional

from .crypto_utils import ClientCrypto


class MessageReceiver:
    """
    Client for receiving encrypted messages
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize message receiver
        
        Args:
            server_url: URL of the secure messenger server
        """
        self.server_url = server_url.rstrip('/')
        self.crypto = ClientCrypto()
    
    def generate_keys(self) -> bool:
        """
        Generate new keypair for this receiver
        
        Returns:
            True if keys were generated and saved successfully
        """
        try:
            private_key, public_key = self.crypto.generate_new_keypair(save_to_file=True)
            print("🔑 New keypair generated successfully!")
            print(f"📄 Public key: {public_key}")
            print(f"🔒 Private key saved to: keys/keys.json")
            print(f"🏷️  Routing token: {self.crypto.get_token()}")
            
            # Export public key for sharing
            if self.crypto.export_public_key():
                print(f"📤 Public key exported to: keys/public_key.txt")
            
            return True
        except Exception as e:
            print(f"❌ Error generating keys: {e}")
            return False
    
    def load_keys(self) -> bool:
        """
        Load existing keys from file
        
        Returns:
            True if keys were loaded successfully
        """
        if self.crypto.load_keys():
            print("🔑 Keys loaded successfully!")
            print(f"📄 Public key: {self.crypto.get_public_key()}")
            print(f"🏷️  Routing token: {self.crypto.get_token()}")
            return True
        else:
            print("❌ No keys found. Generate new keys first.")
            return False
    
    async def poll_messages(
        self,
        since: Optional[float] = None,
        consume: bool = False
    ) -> List[Dict]:
        """
        Poll for messages from the server
        
        Args:
            since: Only return messages after this timestamp
            consume: If True, delete messages after reading
            
        Returns:
            List of decrypted messages
        """
        if not self.crypto.get_token():
            print("❌ No keys loaded. Load keys first.")
            return []
        
        try:
            # Prepare request payload
            payload = {
                "token": self.crypto.get_token(),
                "since": since
            }
            
            # Choose endpoint based on consume flag
            endpoint = "consume" if consume else "poll"
            
            # Poll server for messages using urllib
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.server_url}/api/v1/{endpoint}",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    encrypted_messages = data.get("messages", [])
                    
                    # Decrypt messages
                    decrypted_messages = []
                    for msg in encrypted_messages:
                        try:
                            plaintext = self.crypto.decrypt_message_for_me(
                                msg["sender_public_key"],
                                msg["nonce"],
                                msg["ciphertext"]
                            )
                            
                            decrypted_messages.append({
                                "message_id": msg["message_id"],
                                "message": plaintext,
                                "timestamp": msg["timestamp"],
                                "sender_public_key": msg["sender_public_key"]
                            })
                        except Exception as e:
                            print(f"⚠️  Failed to decrypt message {msg['message_id']}: {e}")
                    
                    return decrypted_messages
                else:
                    print(f"❌ Failed to poll messages: {response.status}")
                    print(f"Response: {response.read().decode('utf-8')}")
                    return []
                    
        except Exception as e:
            print(f"❌ Error polling messages: {e}")
            return []
    
    async def listen_for_messages(self, poll_interval: int = 10):
        """
        Continuously listen for new messages
        
        Args:
            poll_interval: Seconds between polls
        """
        print(f"👂 Listening for messages (polling every {poll_interval}s)...")
        print("Press Ctrl+C to stop")
        print()
        
        last_check = time.time()
        
        try:
            while True:
                messages = await self.poll_messages(since=last_check)
                
                if messages:
                    print(f"📨 Received {len(messages)} new message(s):")
                    print("-" * 50)
                    
                    for msg in messages:
                        print(f"📧 Message ID: {msg['message_id']}")
                        print(f"💬 Content: {msg['message']}")
                        print(f"🕐 Timestamp: {time.ctime(msg['timestamp'])}")
                        print(f"🔑 Sender Key: {msg['sender_public_key'][:16]}...")
                        print("-" * 50)
                
                last_check = time.time()
                await asyncio.sleep(poll_interval)
                
        except KeyboardInterrupt:
            print("\n👋 Stopped listening for messages")


async def main():
    """
    Command-line interface for receiving messages
    """
    parser = argparse.ArgumentParser(description="Receive encrypted messages")
    parser.add_argument(
        "--generate-keys",
        action="store_true",
        help="Generate new keypair"
    )
    parser.add_argument(
        "--check-messages",
        action="store_true",
        help="Check for messages once and exit"
    )
    parser.add_argument(
        "--listen",
        action="store_true",
        help="Continuously listen for messages"
    )
    parser.add_argument(
        "--consume",
        action="store_true",
        help="Delete messages after reading"
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Polling interval in seconds (default: 10)"
    )
    
    args = parser.parse_args()
    
    print("🔐 Secure Messenger - Message Receiver")
    print("=" * 40)
    
    # Initialize receiver
    receiver = MessageReceiver(args.server)
    
    if args.generate_keys:
        receiver.generate_keys()
        return
    
    # Load existing keys
    if not receiver.load_keys():
        print("💡 Run with --generate-keys to create new keys")
        return
    
    if args.check_messages:
        print("📬 Checking for messages...")
        messages = await receiver.poll_messages(consume=args.consume)
        
        if messages:
            print(f"📨 Found {len(messages)} message(s):")
            print("-" * 50)
            
            for msg in messages:
                print(f"📧 Message ID: {msg['message_id']}")
                print(f"💬 Content: {msg['message']}")
                print(f"🕐 Timestamp: {time.ctime(msg['timestamp'])}")
                print(f"🔑 Sender Key: {msg['sender_public_key'][:16]}...")
                print("-" * 50)
        else:
            print("📭 No messages found")
    
    elif args.listen:
        await receiver.listen_for_messages(args.poll_interval)
    
    else:
        print("💡 Use --check-messages or --listen to receive messages")
        print("💡 Use --generate-keys to create new keys")


if __name__ == "__main__":
    asyncio.run(main()) 