"""
Logger configuration for permit-fastmcp package.

This module sets up logging for the middleware and related components.
Import this module to ensure consistent logging configuration across the
package.
"""

import logging

# Configure the root logger for the package
logger = logging.getLogger("permit_fastmcp")
logger.setLevel(logging.INFO)

# Add a default stream handler if not already present
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def setup_logging(level: str = "INFO", format_string: str = None, logger_name: str = "permit_fastmcp"):
    """Set up logging configuration for the package."""
    if format_string is None:
        format_string = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    
    # Configure the root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        force=True
    )
    
    # Configure the package logger
    package_logger = logging.getLogger(logger_name)
    package_logger.setLevel(getattr(logging, level.upper()))
    
    # Add handler if not present
    if not package_logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        package_logger.addHandler(handler)
    
    return package_logger
