import json
import logging
import os
import subprocess
import time
import requests
<<<<<<< HEAD
from configparser import ConfigParser
import cloudinary
import cloudinary.uploader
from filelock import FileLock
from urllib.parse import urlparse, parse_qs, urlencode  # Tambah import ini

# Direktori
DATA_DIR = "data"
TEMP_IMAGES_DIR = "temp_images"
LOG_DIR = "logs"
QUEUE_FILE = "queue.json"

# Setup direktori
=======
import shutil
from configparser import ConfigParser
import cloudinary
import cloudinary.uploader
from urllib.parse import urlparse

DATA_DIR = "data"
TEMP_IMAGES_DIR = "temp_images"
LOG_DIR = "logs"
QUEUE_FILE = os.path.join(DATA_DIR, "queue.json")

>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
for directory in [DATA_DIR, TEMP_IMAGES_DIR, LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

<<<<<<< HEAD
# Load konfigurasi
=======
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
config = ConfigParser()
config.read("config.ini")
CLOUDINARY_CLOUD_NAME = config.get("Cloudinary", "CloudName")
CLOUDINARY_API_KEY = config.get("Cloudinary", "ApiKey")
CLOUDINARY_API_SECRET = config.get("Cloudinary", "ApiSecret")
<<<<<<< HEAD
GITHUB_TOKEN = config.get("GitHub", "GitHubToken")
=======
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or config.get("GitHub", "GitHubToken", fallback="")
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
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

<<<<<<< HEAD
def fetch_page(url, retries=3, delay=2):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
=======
def fetch_page(url, retries=5, delay=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://komiku.org/"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
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
<<<<<<< HEAD
    # Hapus promo phrases
=======
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
    promo_phrases = ["baca komik", "bahasa indonesia", "di komiku"]
    synopsis = original_synopsis.lower()
    for phrase in promo_phrases:
        synopsis = synopsis.replace(phrase, "").strip()
<<<<<<< HEAD
    # Gaya gaul: singkat, santai, pake kata-kata anak muda
    words = synopsis.split()
    if len(words) > 50:
        synopsis = " ".join(words[:50]) + "..."
    # Ganti frase formal ke gaul
=======
    words = synopsis.split()
    if len(words) > 50:
        synopsis = " ".join(words[:50]) + "..."
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
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
<<<<<<< HEAD
    # Tambah vibe gaul
=======
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
    synopsis = synopsis.replace(".", ", bro!").capitalize()
    if not synopsis.endswith("bro!"):
        synopsis += ", bro!"
    logging.info(f"Sinopsis asli: {original_synopsis[:100]}...")
    logging.info(f"Sinopsis gaul: {synopsis}")
    return synopsis

def read_json(file_path):
<<<<<<< HEAD
    lock = FileLock(file_path + ".lock")
    with lock:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

def write_json(file_path, data):
    lock = FileLock(file_path + ".lock")
    with lock:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
=======
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        logging.info(f"[CHECKPOINT] File {file_path} tidak ada, kembalikan list kosong")
        return []
    except Exception as e:
        logging.error(f"[ERROR] Gagal baca {file_path}: {e}")
        return []

def write_json(file_path, data):
    try:
        if os.path.exists(file_path):
            backup_path = file_path + ".backup"
            shutil.copy(file_path, backup_path)
            logging.info(f"[CHECKPOINT] Backup dibuat: {backup_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logging.info(f"[CHECKPOINT] Berhasil menulis ke {file_path}")
    except Exception as e:
        logging.error(f"[ERROR] Gagal menulis {file_path}: {e}")

def add_to_queue(task):
    try:
        logging.info(f"[CHECKPOINT] Menambah tugas ke queue: {task}")
        queue = read_json(QUEUE_FILE)
        if not isinstance(queue, list):
            logging.warning(f"queue.json rusak, reset ke []")
            queue = []
        queue.append(task)
        write_json(QUEUE_FILE, queue)
        logging.info(f"[CHECKPOINT] Tugas ditambahkan ke queue: {task}")
    except Exception as e:
        logging.error(f"[ERROR] Gagal menambah tugas: {task}, error: {e}")
        print(f"Error menambahkan ke queue: {e}")
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390

def upload_to_cloudinary(image_url, comic_id, chapter_num):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
<<<<<<< HEAD
        # Bersihin query parameter dari URL
=======
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
        parsed_url = urlparse(image_url)
        image_name = os.path.basename(parsed_url.path)
        temp_path = os.path.join(TEMP_IMAGES_DIR, image_name)
        with open(temp_path, "wb") as f:
            f.write(response.content)
<<<<<<< HEAD
        # Ubah folder structure biar konsisten
        folder = f"greedycomichub/{comic_id}/chapter_{chapter_num}" if chapter_num != "cover" else f"greedycomichub/{comic_id}/cover"
=======
        folder = f"greedycomics/{comic_id}/chapter_{chapter_num}" if chapter_num != "cover" else f"greedycomics/{comic_id}/cover"
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
        upload_result = cloudinary.uploader.upload(
            temp_path,
            folder=folder,
            overwrite=True,
            resource_type="image"
        )
        os.remove(temp_path)
<<<<<<< HEAD
        logging.info(f"Gambar {image_name} diupload ke Cloudinary: {upload_result['secure_url']}")
        return upload_result["secure_url"]
    except Exception as e:
        logging.error(f"Gagal upload gambar {image_url}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return image_url  # Fallback ke URL asli

def push_to_github():
    logging.info("Push perubahan ke GitHub...")
=======
        logging.info(f"Upload {image_name}: {upload_result['secure_url']}")
        return upload_result["secure_url"]
    except Exception as e:
        logging.error(f"Error upload {image_url}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return image_url

def push_to_github():
    logging.info("Push ke GitHub...")
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
    try:
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
<<<<<<< HEAD
            logging.info("Tidak ada perubahan. Skip push.")
            return True
        subprocess.run(["git", "commit", "-m", "Update comic data"], check=True)
        subprocess.run(
            ["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", "main"],
            check=True
        )
        logging.info("Berhasil push ke GitHub.")
        return True
=======
            logging.info("No changes. Skip push.")
            return True
        subprocess.run(["git", "commit", "-m", "Update comic data"], check=True)
        if not GITHUB_TOKEN:
            logging.error("No GitHub token. Set GITHUB_TOKEN.")
            return False
        logging.info(f"Push ke {GITHUB_REPO}...")
        subprocess.run(
            ["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", "main"],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info("Push sukses.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error push: {e}")
        return False
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
    except Exception as e:
        logging.error(f"Error push: {e}")
        return False