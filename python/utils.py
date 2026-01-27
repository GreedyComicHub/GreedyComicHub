import json
import logging
import os
import subprocess
import time
import requests
import shutil
from configparser import ConfigParser
from filelock import FileLock
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, urlencode

# Root directory and paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.ini")

# Direktori - relative to ROOT
DATA_DIR = os.path.join(ROOT_DIR, "data")
TEMP_IMAGES_DIR = os.path.join(ROOT_DIR, "temp_images")
LOG_DIR = os.path.join(ROOT_DIR, "logs")
QUEUE_FILE = os.path.join(ROOT_DIR, "queue.json")

# Setup direktori
for directory in [DATA_DIR, TEMP_IMAGES_DIR, LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# File lock for thread-safe JSON operations
_lock_file = os.path.join(QUEUE_FILE + ".lock")
lock = FileLock(_lock_file)

# Load konfigurasi - robust with fallback
def _load_github_credentials():
    """Load GitHub credentials from env var or config.ini with robust fallback."""
    # Try environment variable first
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        logging.info(f"✓ Loaded GitHub token from environment variable GITHUB_TOKEN")
        return github_token, None
    
    # Try config.ini
    if not os.path.exists(CONFIG_PATH):
        error_msg = (
            f"\n❌ Config file not found at: {CONFIG_PATH}\n"
            f"Please create config.ini in the root repo with:\n"
            f"[GitHub]\n"
            f"GitHubToken=your_personal_access_token\n"
            f"GitHubRepo=owner/repo\n"
            f"\nOR set environment variable: GITHUB_TOKEN=your_token"
        )
        raise FileNotFoundError(error_msg)
    
    config = ConfigParser()
    config.read(CONFIG_PATH)
    
    try:
        github_token = config.get("GitHub", "GitHubToken")
        logging.info(f"✓ Loaded GitHub token from config.ini at: {CONFIG_PATH}")
        return github_token, config
    except Exception as e:
        error_msg = (
            f"\n❌ Failed to load GitHub credentials from {CONFIG_PATH}\n"
            f"Error: {e}\n"
            f"Ensure config.ini has:\n"
            f"[GitHub]\n"
            f"GitHubToken=your_token\n"
            f"GitHubRepo=owner/repo\n"
            f"\nOR set environment variable: GITHUB_TOKEN"
        )
        raise ValueError(error_msg) from e

# Load credentials
try:
    GITHUB_TOKEN, _config = _load_github_credentials()
    if _config:
        GITHUB_REPO = _config.get("GitHub", "GitHubRepo", fallback="")
    else:
        GITHUB_REPO = os.getenv("GITHUB_REPO", "GreedyComicHub/GreedyComicHub")
except (FileNotFoundError, ValueError) as e:
    logging.error(str(e))
    GITHUB_TOKEN = None
    GITHUB_REPO = None

def setup_logging():
    LOG_FILE = os.path.join(LOG_DIR, "update.log")
    if os.path.exists(LOG_FILE):
        backup_file = os.path.join(LOG_DIR, "update.log.1")
        try:
            if os.path.exists(backup_file):
                os.remove(backup_file)
            shutil.move(LOG_FILE, backup_file)
        except (OSError, PermissionError):
            # If file is locked or can't be moved, just append to it
            pass
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def fetch_page(url: str, retries: int = 3, delay: int = 2) -> Optional[str]:
    """Fetch page content with retry logic.
    
    Args:
        url: Page URL to fetch.
        retries: Number of retry attempts.
        delay: Delay between retries (seconds).
        
    Returns:
        HTML content or None on failure.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            logging.debug(f"Successfully fetched {url} on attempt {attempt + 1}")
            return response.text
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))  # Exponential backoff
        except requests.exceptions.ConnectionError as e:
            logging.warning(f"Connection error for {url} (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
        except requests.RequestException as e:
            logging.warning(f"Failed to fetch {url} (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    logging.error(f"Failed to fetch {url} after {retries} attempts")
    return None

def paraphrase_synopsis(original_synopsis: str) -> str:
    """Convert synopsis to casual Indonesian style.
    
    Args:
        original_synopsis: Original synopsis text.
        
    Returns:
        Paraphrased synopsis with casual tone.
    """
    if not original_synopsis or original_synopsis == "No synopsis available.":
        return "Petualangan seru di dunia penuh aksi dan misteri, bro!"
    promo_phrases = ["baca komik", "bahasa indonesia", "di komiku"]
    synopsis = original_synopsis.lower()
    for phrase in promo_phrases:
        synopsis = synopsis.replace(phrase, "").strip()
    words = synopsis.split()
    if len(words) > 50:
        synopsis = " ".join(words[:50]) + "..."
    replacements = {
        "mengikuti petualangan": "ngejar petualangan",
        "bermimpi menjadi": "nggak sabar jadi",
        "menemukan harta karun": "nyari harta karun",
        "membentuk kru": "ngumpulin geng",
        "menghadapi berbagai rintangan": "ngehadepin macem-macem drama",
        "musuh tangguh": "musuh kece",
        "persahabatan": "bromance",
        "keberanian": "nyali gede",
        "pemerintah dunia": "bos dunia",
        "luas": "buesar"
    }
    for formal, gaul in replacements.items():
        synopsis = synopsis.replace(formal, gaul)
    synopsis = synopsis.replace(".", ", bro!").capitalize()
    if not synopsis.endswith("bro!"):
        synopsis += ", bro!"
    logging.info(f"Sinopsis asli: {original_synopsis[:100]}...")
    logging.info(f"Sinopsis gaul: {synopsis}")
    return synopsis

def read_json(file_path: str) -> Dict[str, Any]:
    """Read JSON file with file lock.
    
    Args:
        file_path: Path to JSON file.
        
    Returns:
        Parsed JSON data or empty dict.
    """
    with lock:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

def write_json(file_path: str, data: Dict[str, Any]) -> None:
    """Write data to JSON file with file lock.
    
    Args:
        file_path: Path to JSON file.
        data: Data to write.
    """
    with lock:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

def push_to_github() -> bool:
    """Push git changes to GitHub repository.
    
    Returns:
        True if push successful, False otherwise.
    """
    try:
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            logging.info("Tidak ada perubahan. Skip push.")
            return True
        subprocess.run(["git", "commit", "-m", "Update comic data"], check=True)
        subprocess.run(
            ["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", "main"],
            check=True
        )
        logging.info("Berhasil push ke GitHub.")
        return True
    except Exception as e:
        logging.error(f"Error push: {e}")
        return False

def get_comic_id_from_url(url: str) -> str:
    """Extract comic ID from URL.
    
    Args:
        url: Comic URL.
        
    Returns:
        Comic ID string.
    """
    logging.info(f"Nama komik dari URL: ID={comic_id}, Display={comic_id.capitalize()}")
    return comic_id