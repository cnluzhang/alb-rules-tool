"""Logging configuration for the ALB Rules Tool."""

import logging
import os
from typing import Optional

def setup_logger(log_level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """Set up and configure logger.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        
    Returns:
        Configured logger instance
    """
    # Get log level from environment if not provided
    if not log_level:
        log_level = os.environ.get("ALB_RULES_LOG_LEVEL", "INFO")
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure logger
    logger = logging.getLogger("alb_rules_tool")
    logger.setLevel(numeric_level)
    logger.propagate = False
    
    # Clear existing handlers to avoid duplicate logs
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
