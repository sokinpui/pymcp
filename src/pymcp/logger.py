# src/pymcp/logger.py
"""
Centralized logging configuration for the PyMCP application.
"""
import logging
import sys


def setup_logging(level=logging.INFO):
    """
    Configures logging for the application.

    This should be called once at the application's entry point.

    Args:
        level: The minimum logging level to output. Defaults to logging.INFO.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=level, stream=sys.stdout, format=log_format)

