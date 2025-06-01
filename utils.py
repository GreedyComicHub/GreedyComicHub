"""Utility functions for GreedyComicHub."""
import json
import os
import re
import time
import logging
import configparser
import git
import cloudinary
import cloudinary.uploader
from filelock import FileLock

def read_json(file_path: str) -> dict:
    """Read JSON file and return its content."""
    try:
        if not os.path.exists(file_path):
            # Buat file kosong kalau nggak ada
            if file_path == "queue.json":
                write_json(file_path, [])
                logging.info(f"Created empty {file_path}")
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")
        return {}

def write_json(file_path: str, data: dict) -> None:
    """Write data to JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Berhasil simpan ke {file_path}")
    except Exception as e:
        logging.error(f"Error writing {file_path}: {str(e)}")
        raise

def setup_cloudinary() -> None:
    """Configure Cloudinary with credentials from config.ini."""
    config = read_config()
    try:
        cloudinary.config(
            cloud_name=config["Cloudinary"]["CloudName"],
            api_key=config["Cloudinary"]["ApiKey"],
            api_secret=config["Cloudinary"]["ApiSecret"]
        )
        logging.info(f"Menggunakan akun Cloudinary: {config['Cloudinary']['CloudName']}")
    except KeyError as e:
        logging.error(f"Cloudinary config missing: {str(e)}")
        raise

def upload_image(image_url: str, folder: str) -> str:
    """Upload image to Cloudinary and return secure URL."""
    try:
        response = cloudinary.uploader.upload(
            image_url,
            folder=f"greedycomichub/{folder}",
            resource_type="image"
        )
        return response["secure_url"]
    except Exception as e:
        logging.error(f"Error uploading image {image_url}: {str(e)}")
        raise

def read_config() -> configparser.ConfigParser:
    """Read config.ini and return ConfigParser object."""
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config

def git_push() -> None:
    """Commit and push changes to GitHub."""
    try:
        config = read_config()
        repo = git.Repo(".")
        repo.git.add(".")
        repo.index.commit(f"Update komik: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        origin = repo.remote(name="origin")
        origin.push()
        logging.info("Berhasil push ke GitHub")
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {str(e)}")
        raise

def get_comic_id_from_url(url: str) -> tuple:
    """Extract comic ID and display name from URL."""
    match = re.search(r"manga/([^/]+)/?$", url)
    if match:
        comic_id = match.group(1)
        display_name = comic_id.replace("-", " ").title()
        return comic_id, display_name
    return None, None

def add_to_queue(task_type: str, task_data: dict) -> None:
    """Add task to queue.json with file lock."""
    queue_file = "queue.json"
    lock = FileLock(queue_file + ".lock")
    with lock:
        queue = read_json(queue_file) or []
        queue.append({
            "type": task_type,
            "data": task_data,
            "status": "pending",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        write_json(queue_file, queue)
    logging.info(f"Added to queue: {task_type} - {task_data}")