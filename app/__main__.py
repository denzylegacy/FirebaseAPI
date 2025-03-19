#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

original_stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

sys.stderr = original_stderr

import uvicorn
import argparse
from dotenv import load_dotenv

load_dotenv()


def main():
    """
    Main entry point for running the application.
    Allows command line arguments to override default settings.
    """
    parser = argparse.ArgumentParser(description="Run the Firebase API server")
    
    parser.add_argument(
        "--host", 
        type=str, 
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.getenv("PORT", "8000")),
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true",
        default=os.getenv("RELOAD", "True").lower() == "true",
        help="Enable auto-reload on code changes (default: True)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting server on {args.host}:{args.port} (reload: {args.reload})")
    
    uvicorn.run(
        "app.api.main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload
    )


if __name__ == "__main__":
    main()
