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
