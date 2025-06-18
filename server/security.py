"""
Security middleware and utilities for the secure messenger server
Protects against brute force attacks, DoS, and other threats
"""

import time
import hashlib
from typing import Dict, Set, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

# In-memory stores for security tracking
failed_attempts: Dict[str, int] = {}
blocked_ips: Set[str] = {}
last_cleanup = time.time()

# Security configuration
MAX_FAILED_ATTEMPTS = 5
BLOCK_DURATION = 300  # 5 minutes in seconds
CLEANUP_INTERVAL = 60  # 1 minute
SUSPICIOUS_PATHS = {
    "/admin", "/wp-admin", "/phpmyadmin", "/mysql", 
    "/login", "/ssh", "/.env", "/config", "/backup",
    "/wp-login", "/administrator", "/panel", "/cpanel"
}


def cleanup_security_data():
    """
    Clean up old security data periodically
    """
    global last_cleanup, failed_attempts, blocked_ips
    
    current_time = time.time()
    if current_time - last_cleanup < CLEANUP_INTERVAL:
        return
    
    # Clean up old failed attempts (older than block duration)
    cutoff_time = current_time - BLOCK_DURATION
    failed_attempts = {
        ip: count for ip, count in failed_attempts.items()
        if count < MAX_FAILED_ATTEMPTS
    }
    
    # Clean up expired IP blocks
    # For simplicity, we'll reset blocked IPs periodically
    # In production, you'd want more sophisticated tracking
    if current_time - last_cleanup > BLOCK_DURATION:
        blocked_ips.clear()
    
    last_cleanup = current_time


def is_ip_blocked(ip: str) -> bool:
    """
    Check if an IP is currently blocked
    """
    cleanup_security_data()
    return ip in blocked_ips


def record_failed_attempt(ip: str):
    """
    Record a failed attempt and block IP if threshold exceeded
    """
    cleanup_security_data()
    
    failed_attempts[ip] = failed_attempts.get(ip, 0) + 1
    
    if failed_attempts[ip] >= MAX_FAILED_ATTEMPTS:
        blocked_ips.add(ip)
        print(f"🚫 Blocked suspicious IP: {ip} (too many failed attempts)")


def is_suspicious_request(request: Request) -> bool:
    """
    Detect suspicious requests (scanners, bots, etc.)
    """
    path = request.url.path.lower()
    
    # Check for common attack paths
    if any(suspicious in path for suspicious in SUSPICIOUS_PATHS):
        return True
    
    # Check for suspicious user agents
    user_agent = request.headers.get("user-agent", "").lower()
    suspicious_agents = ["scanner", "bot", "crawler", "sqlmap", "nikto", "nmap"]
    if any(agent in user_agent for agent in suspicious_agents):
        return True
    
    # Check for SQL injection attempts in path
    sql_patterns = ["union", "select", "drop", "insert", "delete", "'", '"', ";"]
    if any(pattern in path for pattern in sql_patterns):
        return True
    
    return False


def validate_api_request(request: Request) -> bool:
    """
    Validate that the request is a legitimate API call
    """
    path = request.url.path
    
    # Only allow specific endpoints
    allowed_paths = {
        "/", "/docs", "/redoc", "/openapi.json",
        "/api/v1/send", "/api/v1/poll", "/api/v1/consume",
        "/api/v1/status", "/api/v1/health", "/health"
    }
    
    if path not in allowed_paths:
        return False
    
    # Check content type for POST requests
    if request.method == "POST":
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return False
    
    return True


async def security_middleware(request: Request, call_next):
    """
    Main security middleware
    """
    client_ip = get_remote_address(request)
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        print(f"🚫 Blocked request from {client_ip}")
        raise HTTPException(status_code=429, detail="IP temporarily blocked")
    
    # Check for suspicious requests
    if is_suspicious_request(request):
        record_failed_attempt(client_ip)
        print(f"🚨 Suspicious request from {client_ip}: {request.url.path}")
        raise HTTPException(status_code=404, detail="Not found")
    
    # Validate API requests
    if not validate_api_request(request):
        record_failed_attempt(client_ip)
        print(f"⚠️ Invalid API request from {client_ip}: {request.url.path}")
        raise HTTPException(status_code=404, detail="Not found")
    
    # Process the request
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Record failed attempts on errors
        if hasattr(e, 'status_code') and e.status_code >= 400:
            record_failed_attempt(client_ip)
        raise


def get_security_stats() -> Dict:
    """
    Get current security statistics
    """
    cleanup_security_data()
    
    return {
        "blocked_ips_count": len(blocked_ips),
        "failed_attempts_tracked": len(failed_attempts),
        "max_failed_attempts": MAX_FAILED_ATTEMPTS,
        "block_duration_seconds": BLOCK_DURATION
    } 