from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from typing import List, Union
import logging

logger = logging.getLogger("authorization_service")

def setup_cors(app: FastAPI, allow_origins: List[str] = ["*"]) -> None:
    """
    Configure CORS middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        allow_origins: List of allowed origins (defaults to ["*"])
    """
    logger.info(f"Configuring CORS with allowed origins: {', '.join(allow_origins) if allow_origins else 'None'}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Log successful CORS setup
    logger.info("CORS middleware successfully configured")
