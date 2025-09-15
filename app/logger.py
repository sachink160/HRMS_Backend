import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("hrms.log")
    ]
)

logger = logging.getLogger("hrms")

def log_info(message: str):
    logger.info(message)

def log_error(message: str):
    logger.error(message)

def log_warning(message: str):
    logger.warning(message)
