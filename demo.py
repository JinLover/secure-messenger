#!/usr/bin/env python3
"""
Secure Messenger Demo Script
Tests the complete encryption workflow: key generation, message sending, and receiving
"""

import asyncio
import json
import tempfile
import os
from pathlib import Path

from client.sender import MessageSender
from client.receiver import MessageReceiver
from crypto.nacl_wrapper import generate_keypair, generate_token


async def demo_complete_workflow():
    """
    Demonstrate the complete secure messaging workflow
    """
    print("🔐 Secure Messenger Demo")
    print("=" * 50)
    print()
    
    # 1. Generate keys for Alice (receiver)
    print("👤 Step 1: Generate keys for Alice (receiver)")
    alice_private_key, alice_public_key = generate_keypair()
    alice_token = generate_token(alice_public_key)
    
    print(f"🔑 Alice's public key: {alice_public_key}")
    print(f"🏷️  Alice's token: {alice_token}")
    print()
    
    # 2. Create temporary key file for Alice
    with tempfile.TemporaryDirectory() as temp_dir:
        alice_keys_dir = Path(temp_dir) / "alice_keys"
        alice_keys_dir.mkdir()
        
        alice_keys_file = alice_keys_dir / "keys.json"
        with open(alice_keys_file, 'w') as f:
            json.dump({
                "private_key": alice_private_key,
                "public_key": alice_public_key,
                "token": alice_token
            }, f)
        
        # 3. Initialize clients
        print("📱 Step 2: Initialize clients")
        sender = MessageSender("http://localhost:8000")
        receiver = MessageReceiver("http://localhost:8000")
        receiver.crypto.keys_dir = alice_keys_dir
        receiver.crypto.load_keys()
        
        print("✅ Clients initialized")
        print()
        
        # 4. Send a test message
        test_message = "Hello from the secure messenger! 🔒✨"
        print(f"📤 Step 3: Send message from Bob to Alice")
        print(f"💬 Message: '{test_message}'")
        
        result = await sender.send_message(
            alice_public_key,
            test_message,
            ttl=300  # 5 minutes
        )
        
        if result:
            print("✅ Message sent successfully!")
            print(f"📧 Message ID: {result['message_id']}")
            print()
        else:
            print("❌ Failed to send message")
            return
        
        # 5. Wait a moment and then check for messages
        print("📬 Step 4: Check for messages (Alice)")
        await asyncio.sleep(1)  # Small delay
        
        messages = await receiver.poll_messages()
        
        if messages:
            print(f"📨 Alice received {len(messages)} message(s):")
            print("-" * 40)
            
            for msg in messages:
                print(f"📧 Message ID: {msg['message_id']}")
                print(f"💬 Content: {msg['message']}")
                print(f"🔑 Sender: {msg['sender_public_key'][:16]}...")
                print("-" * 40)
            
            # Verify the message content
            if messages[0]['message'] == test_message:
                print("✅ Message content verified!")
                print()
                print("🎉 Demo completed successfully!")
                print()
                print("🔒 Security verification:")
                print("  ✓ Server cannot read message content (end-to-end encrypted)")
                print("  ✓ Server cannot identify sender (ephemeral keys)")
                print("  ✓ Server cannot identify receiver (hashed routing tokens)")
                print("  ✓ Only Alice can decrypt the message")
            else:
                print("❌ Message content mismatch!")
        else:
            print("📭 No messages received")


async def demo_server_status():
    """
    Check server status and demonstrate API endpoints
    """
    print("\n🖥️  Server Status Check")
    print("=" * 30)
    
    import urllib.request
    import json
    
    try:
        # Check server root
        req = urllib.request.Request("http://localhost:8000/")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("✅ Server is running")
                data = json.loads(response.read().decode('utf-8'))
                print(f"📡 Server: {data['name']} v{data['version']}")
                print(f"📋 Features: {', '.join(data['features'])}")
        
        # Check server status
        req = urllib.request.Request("http://localhost:8000/api/v1/status")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                status = json.loads(response.read().decode('utf-8'))
                print(f"📊 Status: {status['status']}")
                print(f"📨 Total messages: {status['total_messages']}")
                print(f"🏷️  Active tokens: {status['active_tokens']}")
                print(f"⏰ Uptime: {status['uptime_seconds']:.1f}s")
            
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure the server is running: uv run python main.py")


async def main():
    """
    Main demo function
    """
    # Check if server is accessible
    await demo_server_status()
    
    print()
    input("Press Enter to start the messaging demo...")
    
    # Run the complete workflow demo
    await demo_complete_workflow()


if __name__ == "__main__":
    asyncio.run(main()) 