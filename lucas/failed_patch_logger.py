import json
import logging
import os
import tempfile
from datetime import datetime

class FailedPatchLogger:
    def __init__(self):
        self.log_dir = os.path.join(tempfile.gettempdir(), "lucas_failed_patches")
        os.makedirs(self.log_dir, exist_ok=True)

    def log_failed_patch(self, patch_content):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"failed_patch_{timestamp}.patch"
        full_path = os.path.join(self.log_dir, filename)

        with open(full_path, 'w') as f:
            f.write(patch_content)
