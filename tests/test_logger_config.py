def test_logger_config_import_and_setup():
    import importlib
    import sys
    import logging

    # Remove from sys.modules to force re-import and handler setup
    sys.modules.pop("permit_fastmcp.logger_config", None)
    # Remove all handlers for the logger
    logger = logging.getLogger("permit_fastmcp")
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    logger_config = importlib.import_module("permit_fastmcp.logger_config")
    logger = logger_config.logger
    logger.info("Logger config test message")
    assert logger.name == "permit_fastmcp"
    assert logger.hasHandlers()
