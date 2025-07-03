import logging

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    # Optionally set Starlette/Uvicorn log levels
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("starlette").setLevel(level) 
    