import logging
import os
from logging.handlers import RotatingFileHandler

def setup_request_logger(log_file='request_response.log', max_file_size=10*1024*1024, backup_count=5):
    logger = logging.getLogger('request_response_logger')
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Use RotatingFileHandler to manage log file size
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_file_size,  # 10 MB
        backupCount=backup_count
    )
    
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger

chat_logger = setup_request_logger(log_file='/tmp/lucas_requests.log')
