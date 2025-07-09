from pathlib import Path
import os
from datetime import datetime

def get_project_root() -> Path:
    current = Path(__file__).resolve().parent.parent
    return current

PROJECT_ROOT = get_project_root()
today_date_folder = datetime.now().strftime("%Y_%m_%d")
VIDEO_OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "output","media","video", today_date_folder)
VOICE_OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "output","media","voie", today_date_folder)
IMAGES_OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "output","media","images", today_date_folder)
TEMPLATE_LIBRARY_FOLDER = os.path.join(PROJECT_ROOT, "prompt_library")
SCRIPT_OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "output", "script_json")
BACKGROUND_IMAGE_FOLDER = os.path.join(PROJECT_ROOT, "resources", "background")

def debug_print(*args, **kwargs):
    """Print debug information with timestamp and store it in a log file"""
    from datetime import datetime
    import sys
    import os

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] " + " ".join(map(str, args))

    # Print to console
    print(message, **kwargs)
    sys.stdout.flush()

    # Append to log file
    log_file_path = os.path.join(PROJECT_ROOT, "logs", today_date_folder, "debug_log.txt")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")