"""
Logging configuration for IBM BAW MCP Server.

Provides structured logging with proper formatting and log levels.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with ANSI color codes.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string with colors
        """
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname:8}"
                f"{self.COLORS['RESET']}"
            )
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file_path: Optional[str] = None,
    enable_colors: bool = True
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file_path: Optional path to log file
        enable_colors: Enable colored output for console
    """
    # Convert log level string to logging constant
    numeric_log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_log_level)
    
    if enable_colors and sys.stderr.isatty():
        # Use colored formatter for console
        console_log_format = (
            "%(levelname)s | "
            "%(asctime)s | "
            "%(name)s | "
            "%(message)s"
        )
        console_formatter = ColoredFormatter(
            console_log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Use plain formatter
        console_log_format = (
            "%(levelname)-8s | "
            "%(asctime)s | "
            "%(name)s | "
            "%(message)s"
        )
        console_formatter = logging.Formatter(
            console_log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file_path:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(numeric_log_level)
        
        file_log_format = (
            "%(levelname)-8s | "
            "%(asctime)s | "
            "%(name)s | "
            "%(funcName)s:%(lineno)d | "
            "%(message)s"
        )
        file_formatter = logging.Formatter(
            file_log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Log initial message
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"Logging initialized at {log_level} level")
    if log_file_path:
        module_logger.info(f"Logging to file: {log_file_path}")


def get_logger(logger_name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        logger_name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(logger_name)

# Made with Bob
