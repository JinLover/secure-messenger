"""
Secure Messenger - Main Entry Point
Zero-knowledge relay server for encrypted messaging
"""

import os
import sys
import uvicorn
from server.app import app


def main():
    """
    Main entry point for the secure messenger server
    """
    print("🔐 Secure Messenger Server")
    print("📡 Zero-knowledge relay for encrypted messaging")
    print("=" * 50)
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"📊 Log Level: {log_level}")
    print("=" * 50)
    
    try:
        # Run the server
        uvicorn.run(
            "server.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=False  # Minimal logging for privacy
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
