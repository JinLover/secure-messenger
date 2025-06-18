"""
Message storage for the secure messenger server
In-memory storage with TTL support (can be extended to Redis/DB later)
"""

import time
import asyncio
from typing import List, Dict, Optional
from threading import Lock
from .models import EncryptedMessage, MessageResponse


class MessageStorage:
    """
    In-memory message storage with automatic TTL cleanup
    Thread-safe implementation for concurrent access
    """
    
    def __init__(self):
        self._messages: Dict[str, List[EncryptedMessage]] = {}
        self._lock = Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_time = time.time()
        
    async def start_cleanup_task(self):
        """Start the background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
    
    async def stop_cleanup_task(self):
        """Stop the background cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    def store_message(self, message: EncryptedMessage) -> None:
        """
        Store an encrypted message
        
        Args:
            message: The encrypted message to store
        """
        with self._lock:
            if message.token not in self._messages:
                self._messages[message.token] = []
            
            self._messages[message.token].append(message)
    
    def get_messages(
        self, 
        token: str, 
        since: Optional[float] = None,
        delete_after_read: bool = False
    ) -> List[MessageResponse]:
        """
        Retrieve messages for a specific token
        
        Args:
            token: The routing token to retrieve messages for
            since: Only return messages after this timestamp
            delete_after_read: If True, delete messages after reading
            
        Returns:
            List of message responses
        """
        with self._lock:
            if token not in self._messages:
                return []
            
            current_time = time.time()
            messages = self._messages[token]
            
            # Filter messages by timestamp and TTL
            filtered_messages = []
            remaining_messages = []
            
            for msg in messages:
                # Check TTL
                if msg.ttl and (current_time - msg.timestamp) > msg.ttl:
                    continue  # Expired message, skip it
                
                # Check since timestamp
                if since and msg.timestamp <= since:
                    if not delete_after_read:
                        remaining_messages.append(msg)
                    continue
                
                # Message passes filters
                filtered_messages.append(MessageResponse(
                    message_id=msg.message_id,
                    ciphertext=msg.ciphertext,
                    nonce=msg.nonce,
                    sender_public_key=msg.sender_public_key,
                    timestamp=msg.timestamp
                ))
                
                if not delete_after_read:
                    remaining_messages.append(msg)
            
            # Update stored messages if delete_after_read is True
            if delete_after_read:
                if remaining_messages:
                    self._messages[token] = remaining_messages
                else:
                    del self._messages[token]
            else:
                # Still need to remove expired messages
                if remaining_messages:
                    self._messages[token] = remaining_messages
                else:
                    del self._messages[token]
            
            return filtered_messages
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage stats
        """
        with self._lock:
            total_messages = sum(len(msgs) for msgs in self._messages.values())
            active_tokens = len(self._messages)
            uptime = time.time() - self._start_time
            
            return {
                "total_messages": total_messages,
                "active_tokens": active_tokens,
                "uptime_seconds": uptime
            }
    
    async def _cleanup_expired_messages(self):
        """
        Background task to clean up expired messages
        Runs every 60 seconds
        """
        while True:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                current_time = time.time()
                
                with self._lock:
                    tokens_to_remove = []
                    
                    for token, messages in self._messages.items():
                        # Filter out expired messages
                        valid_messages = [
                            msg for msg in messages
                            if not msg.ttl or (current_time - msg.timestamp) <= msg.ttl
                        ]
                        
                        if valid_messages:
                            self._messages[token] = valid_messages
                        else:
                            tokens_to_remove.append(token)
                    
                    # Remove empty token buckets
                    for token in tokens_to_remove:
                        del self._messages[token]
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log the error but continue cleanup
                print(f"Error during message cleanup: {e}")


# Global storage instance
message_storage = MessageStorage() 