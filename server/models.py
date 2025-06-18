"""
Data models for the secure messenger server
"""

import time
from typing import Optional, List
from pydantic import BaseModel, Field


class EncryptedMessage(BaseModel):
    """
    Encrypted message as stored on the server
    Server never sees the plaintext content
    """
    message_id: str = Field(..., description="Unique message identifier")
    token: str = Field(..., description="Routing token (hash of recipient's public key)")
    ciphertext: str = Field(..., description="Encrypted message content as hex")
    nonce: str = Field(..., description="Encryption nonce as hex")
    sender_public_key: str = Field(..., description="Sender's ephemeral public key as hex")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp when message was received")
    ttl: Optional[float] = Field(default=None, description="Time-to-live in seconds")


class SendMessageRequest(BaseModel):
    """
    Request to send an encrypted message
    """
    token: str = Field(..., description="Routing token for the recipient")
    ciphertext: str = Field(..., description="Encrypted message content as hex")
    nonce: str = Field(..., description="Encryption nonce as hex")
    sender_public_key: str = Field(..., description="Sender's ephemeral public key as hex")
    ttl: Optional[int] = Field(default=1800, description="Message TTL in seconds (default: 30 minutes)")


class PollMessagesRequest(BaseModel):
    """
    Request to poll messages for a specific token
    """
    token: str = Field(..., description="Routing token to poll messages for")
    since: Optional[float] = Field(default=None, description="Only return messages after this timestamp")


class MessageResponse(BaseModel):
    """
    Response containing encrypted message(s)
    """
    message_id: str
    ciphertext: str
    nonce: str
    sender_public_key: str
    timestamp: float


class PollMessagesResponse(BaseModel):
    """
    Response to poll messages request
    """
    messages: List[MessageResponse]
    count: int = Field(..., description="Number of messages returned")


class SendMessageResponse(BaseModel):
    """
    Response to send message request
    """
    status: str
    message_id: str
    timestamp: float


class ServerStatusResponse(BaseModel):
    """
    Server status information
    """
    status: str
    version: str
    uptime_seconds: float
    total_messages: int
    active_tokens: int
    auto_cleanup_enabled: bool = Field(default=True, description="Whether automatic message cleanup is enabled")
    default_ttl_minutes: int = Field(default=30, description="Default TTL for messages in minutes") 