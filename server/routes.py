"""
API routes for the secure messenger server
"""

import time
from typing import List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .models import (
    SendMessageRequest,
    SendMessageResponse,
    PollMessagesRequest,
    PollMessagesResponse,
    ServerStatusResponse,
    EncryptedMessage
)
from .storage import message_storage
from crypto.nacl_wrapper import generate_message_id

router = APIRouter()


@router.post("/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
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
            token=request.token,
            ciphertext=request.ciphertext,
            nonce=request.nonce,
            sender_public_key=request.sender_public_key,
            timestamp=time.time(),
            ttl=request.ttl
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
async def poll_messages(request: PollMessagesRequest):
    """
    Poll for messages using a routing token
    
    The server returns encrypted messages for the token
    but cannot decrypt them or identify the recipient
    """
    try:
        # Get messages for the token
        messages = message_storage.get_messages(
            token=request.token,
            since=request.since,
            delete_after_read=False  # Keep messages for multiple polls
        )
        
        return PollMessagesResponse(
            messages=messages,
            count=len(messages)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll messages: {str(e)}")


@router.post("/consume", response_model=PollMessagesResponse)
async def consume_messages(request: PollMessagesRequest):
    """
    Consume messages (poll and delete)
    
    Similar to poll but messages are deleted after being read
    """
    try:
        # Get and delete messages for the token
        messages = message_storage.get_messages(
            token=request.token,
            since=request.since,
            delete_after_read=True  # Delete after reading
        )
        
        return PollMessagesResponse(
            messages=messages,
            count=len(messages)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to consume messages: {str(e)}")


@router.get("/status", response_model=ServerStatusResponse)
async def get_server_status():
    """
    Get server status and statistics
    
    Returns general server health information
    """
    try:
        stats = message_storage.get_stats()
        
        return ServerStatusResponse(
            status="healthy",
            version="0.1.0",
            uptime_seconds=stats["uptime_seconds"],
            total_messages=stats["total_messages"],
            active_tokens=stats["active_tokens"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server status: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint
    """
    return {"status": "healthy", "timestamp": time.time()}


# Rate limiting and security middleware could be added here
# For now, we keep it simple for the MVP 