"""Utility functions for GreedyComicHub."""
import json
import logging
import subprocess
from typing import Any, Dict, Optional, Tuple

def read_json(file_path: str) -> Optional[Dict]:
    """Read JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")
        return None

def write_json(file_path: str, data: Any) -> None:
    """Write JSON file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error writing {file_path}: {str(e)}")
        raise

def get_comic_id_from_url(url: str) -> Tuple[str, str]:
    """Extract comic ID and base URL from comic URL."""
    try:
        if "komiku.org" in url:
            parts = url.rstrip("/").split("/")
            comic_id = parts[-1].replace("manga-", "")
            base_url = "/".join(parts[:-1]) + "/"
            return comic_id, base_url
        return "", ""
    except Exception as e:
        logging.error(f"Error parsing URL {url}: {str(e)}")
        return "", ""

def add_to_queue(task_type: str, task_data: Dict) -> None:
    """Add task to queue.json."""
    queue_file = "queue.json"
    try:
        queue = read_json(queue_file) or []
        queue.append({"type": task_type, "data": task_data, "status": "pending"})
        write_json(queue_file, queue)
        logging.info(f"Added to queue: {task_type} - {task_data}")
    except Exception as e:
        logging.error(f"Error adding to queue: {str(e)}")
        raise

def git_push() -> None:
    """Push changes to GitHub."""
    try:
        subprocess.run(["git", "add", "."], check=True)
        result = subprocess.run(
            ["git", "commit", "-m", "Update comic data"],
            check=True,
            capture_output=True,
            text=True
        )
        if "nothing to commit" not in result.stdout:
            subprocess.run(["git", "push"], check=True)
            logging.info("Berhasil push ke GitHub")
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stdout:
            logging.info("No changes to commit")
        else:
            logging.error(f"Error pushing to GitHub: {str(e)}")
            raise