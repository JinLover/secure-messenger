"""
API routes for the secure messenger server
"""

import time
from typing import List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from .models import (
    SendMessageRequest,
    SendMessageResponse,
    PollMessagesRequest,
    PollMessagesResponse,
    ServerStatusResponse,
    EncryptedMessage
)
from .storage import message_storage
from .security import get_security_stats
from crypto.nacl_wrapper import generate_message_id

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/send", response_model=SendMessageResponse)
@limiter.limit("100/minute")  # Allow 100 messages per minute per IP (10 -> 100)
async def send_message(request: Request, message_request: SendMessageRequest):
    """
    Send an encrypted message to the server
    
    The server stores the message without knowing:
    - The content (it's encrypted)
    - The recipient (token is a hash)
    - The sender (ephemeral key used)
    """
    try:
        # Generate unique message ID
        message_id = generate_message_id()
        
        # Create encrypted message
        encrypted_message = EncryptedMessage(
            message_id=message_id,
            token=message_request.token,
            ciphertext=message_request.ciphertext,
            nonce=message_request.nonce,
            sender_public_key=message_request.sender_public_key,
            timestamp=time.time(),
            ttl=message_request.ttl
        )
        
        # Store the message
        message_storage.store_message(encrypted_message)
        
        return SendMessageResponse(
            status="success",
            message_id=message_id,
            timestamp=encrypted_message.timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/poll", response_model=PollMessagesResponse)
@limiter.limit("100/minute")  # Allow 100 polls per minute per IP (300 -> 100)
async def poll_messages(request: Request, poll_request: PollMessagesRequest):
    """
    Poll for messages using a routing token
    
    The server returns encrypted messages for the token
    but cannot decrypt them or identify the recipient
    """
    try:
        # Get messages for the token
        messages = message_storage.get_messages(
            token=poll_request.token,
            since=poll_request.since,
            delete_after_read=False  # Keep messages for multiple polls
        )
        
        return PollMessagesResponse(
            messages=messages,
            count=len(messages)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll messages: {str(e)}")


@router.post("/consume", response_model=PollMessagesResponse)
@limiter.limit("100/minute")  # Allow 100 consume requests per minute per IP (300 -> 100)
async def consume_messages(request: Request, consume_request: PollMessagesRequest):
    """
    Consume messages (poll and delete)
    
    Similar to poll but messages are deleted after being read
    """
    try:
        # Get and delete messages for the token
        messages = message_storage.get_messages(
            token=consume_request.token,
            since=consume_request.since,
            delete_after_read=True  # Delete after reading
        )
        
        return PollMessagesResponse(
            messages=messages,
            count=len(messages)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to consume messages: {str(e)}")


@router.get("/status", response_model=ServerStatusResponse)
@limiter.limit("60/minute")  # Allow 60 status checks per minute per IP (5 -> 60)
async def get_server_status(request: Request):
    """
    Get server status and statistics
    
    Returns general server health information
    """
    try:
        stats = message_storage.get_stats()
        security_stats = get_security_stats()
        
        return ServerStatusResponse(
            status="healthy",
            version="0.1.0",
            uptime_seconds=stats["uptime_seconds"],
            total_messages=stats["total_messages"],
            active_tokens=stats["active_tokens"],
            auto_cleanup_enabled=True,
            default_ttl_minutes=30,
            security=security_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server status: {str(e)}")


@router.get("/health")
@limiter.limit("120/minute")  # Allow 120 health checks per minute per IP (10 -> 120)
async def health_check(request: Request):
    """
    Simple health check endpoint
    """
    return {"status": "healthy", "timestamp": time.time()}


# Rate limiting and security middleware could be added here
# For now, we keep it simple for the MVP 