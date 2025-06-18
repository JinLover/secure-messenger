"""
Secure Messenger Server
Zero-knowledge relay server for encrypted messaging

The server:
- Cannot decrypt message contents
- Cannot identify senders (ephemeral keys)
- Cannot identify recipients (hashed tokens)
- Only routes encrypted messages based on tokens
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .routes import router
from .storage import message_storage
from .security import security_middleware, limiter, get_security_stats


# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown tasks
    """
    # Startup
    print("🚀 Starting Secure Messenger Server...")
    print("📡 Zero-knowledge relay server initialized")
    
    # Start background cleanup task
    await message_storage.start_cleanup_task()
    print("🧹 Message cleanup task started")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Secure Messenger Server...")
    await message_storage.stop_cleanup_task()
    print("✅ Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="Secure Messenger Server",
    description="Zero-knowledge relay server for end-to-end encrypted messaging",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiting support
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Security middleware (comprehensive protection)
@app.middleware("http")
async def comprehensive_security_middleware(request: Request, call_next):
    """
    Comprehensive security middleware combining multiple protections
    """
    # Apply security checks first
    response = await security_middleware(request, call_next)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Server"] = "SecureMessenger/1.0"  # Hide server details
    
    return response


# Privacy middleware (minimal logging)
@app.middleware("http")
async def privacy_middleware(request: Request, call_next):
    """
    Privacy-focused middleware
    Minimizes logging of sensitive information
    """
    start_time = time.time()
    
    # Don't log request bodies or detailed paths for privacy
    method = request.method
    endpoint = request.url.path
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Minimal logging - only method, endpoint, status, and timing
    print(f"{method} {endpoint} - {response.status_code} - {process_time:.3f}s")
    
    return response


# Exception handling
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# Include API routes
app.include_router(router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with server information
    """
    return {
        "name": "Secure Messenger Server",
        "version": "0.1.0",
        "description": "Zero-knowledge relay server for encrypted messaging",
        "features": [
            "End-to-end encryption",
            "Zero-knowledge server",
            "Anonymous routing",
            "Ephemeral sender keys",
            "Message TTL support"
        ],
        "endpoints": {
            "send": "/api/v1/send",
            "poll": "/api/v1/poll", 
            "consume": "/api/v1/consume",
            "status": "/api/v1/status",
            "health": "/api/v1/health"
        },
        "timestamp": time.time()
    }


# Development helper
if __name__ == "__main__":
    import uvicorn
    
    print("🔧 Running in development mode")
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 