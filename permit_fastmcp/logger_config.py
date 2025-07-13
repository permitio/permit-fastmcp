import logging

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s | %(name)s | %(asctime)s"
    )
    # Optionally set Starlette/Uvicorn log levels
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("starlette").setLevel(level) 
    