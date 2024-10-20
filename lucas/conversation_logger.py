import json
import logging
import os
import tempfile
from datetime import datetime

class ConversationLogger:
    def __init__(self, client_name):
        self.client_name = client_name
        self.log_dir = os.path.join(tempfile.gettempdir(), f"lucas_{client_name}_logs")
        os.makedirs(self.log_dir, exist_ok=True)

    def log_conversation(self, request, response):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.client_name}_{timestamp}.json"
        full_path = os.path.join(self.log_dir, filename)

        conversation = {
            "timestamp": timestamp,
            "request": request,
            "response": response
        }

        with open(full_path, 'w') as f:
            json.dump(conversation, f, indent=2)

        logging.info(f"Conversation logged to: {full_path}")
        return full_path
