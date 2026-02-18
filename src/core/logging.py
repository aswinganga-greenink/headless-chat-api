import logging
import sys
from src.core.config import get_settings

settings = get_settings()

def setup_logging():
    """
    Configures the root logger with a consistent format.
    Adjusts log level based on the DEBUG setting.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Basic configuration for standard output
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silence noisy libraries if needed
    # logging.getLogger("multipart").setLevel(logging.WARNING)
    
    logger = logging.getLogger("chat_api")
    logger.info(f"Logging initialized at level: {logging.getLevelName(log_level)}")
