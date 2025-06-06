import json
import logging
import os
import subprocess
import time
import requests
import shutil
from configparser import ConfigParser
import cloudinary
import cloudinary.uploader
from filelock import FileLock
from urllib.parse import urlparse, parse_qs, urlencode

# Direktori
DATA_DIR = "data"
TEMP_IMAGES_DIR = "temp_images"
LOG_DIR = "logs"
QUEUE_FILE = "queue.json"

# Setup direktori
for directory in [DATA_DIR, TEMP_IMAGES_DIR, LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Load konfigurasi
config = ConfigParser()
config.read("config.ini")
CLOUDINARY_CLOUD_NAME = config.get("Cloudinary", "CloudName")
CLOUDINARY_API_KEY = config.get("Cloudinary", "ApiKey")
CLOUDINARY_API_SECRET = config.get("Cloudinary", "ApiSecret")
GITHUB_TOKEN = config.get("GitHub", "GitHubToken")
GITHUB_REPO = config.get("GitHub", "GitHubRepo")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

def setup_logging():
    LOG_FILE = os.path.join(LOG_DIR, "update.log")
    if os.path.exists(LOG_FILE):
        backup_file = os.path.join(LOG_DIR, "update.log.1")
        if os.path.exists(backup_file):
            os.remove(backup_file)
        os.rename(LOG_FILE, backup_file)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def fetch_page(url, retries=3, delay=2):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.warning(f"Gagal mengambil {url} (percobaan {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    return None

def paraphrase_synopsis(original_synopsis):
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

def read_json(file_path):
    lock = FileLock(file_path + ".lock")
    with lock:
        logging.info(f"[CHECKPOINT] Membaca file: {file_path}")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        logging.info(f"[CHECKPOINT] File {file_path} tidak ada, kembalikan dict kosong")
        return {}

def write_json(file_path, data):
    lock = FileLock(file_path + ".lock")
    with lock:
        logging.info(f"[CHECKPOINT] Menulis ke file: {file_path}")
        if os.path.exists(file_path):
            backup_path = file_path + ".backup"
            shutil.copy(file_path, backup_path)
            logging.info(f"[CHECKPOINT] Backup dibuat: {backup_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logging.info(f"[CHECKPOINT] Berhasil menulis ke {file_path}")

def add_to_queue(task):
    """Tambah tugas ke queue.json dengan aman."""
    lock = FileLock(QUEUE_FILE + ".lock")
    with lock:
        logging.info(f"[CHECKPOINT] Menambah tugas ke queue: {task}")
        queue = read_json(QUEUE_FILE)
        queue.append(task)
        write_json(QUEUE_FILE, queue)
        logging.info(f"[CHECKPOINT] Tugas ditambahkan ke queue: {task}")

def upload_to_cloudinary(image_url, comic_id, chapter_num):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        parsed_url = urlparse(image_url)
        image_name = os.path.basename(parsed_url.path)
        temp_path = os.path.join(TEMP_IMAGES_DIR, image_name)
        with open(temp_path, "wb") as f:
            f.write(response.content)
        folder = f"greedycomichub/{comic_id}/chapter_{chapter_num}" if chapter_num != "cover" else f"greedycomichub/{comic_id}/cover"
        upload_result = cloudinary.uploader.upload(
            temp_path,
            folder=folder,
            overwrite=True,
            resource_type="image"
        )
        os.remove(temp_path)
        logging.info(f"Gambar {image_name} diupload ke Cloudinary: {upload_result['secure_url']}")
        return upload_result["secure_url"]
    except Exception as e:
        logging.error(f"Gagal upload gambar {image_url}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return image_url

def push_to_github():
    logging.info("Push perubahan ke GitHub...")
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