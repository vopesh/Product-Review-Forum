import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Configuration
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create logger
logger = logging.getLogger("photo_video_app")
logger.setLevel(LOG_LEVEL)

# Prevent duplicate handlers if the module is re-imported
if not logger.handlers:
    # Console Handler
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)

    # Rotating File Handler (1MB per file, keeps 5 backups)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
