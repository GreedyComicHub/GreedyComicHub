import json
import logging
import os
import requests
from git import Repo
from threading import Lock
from configparser import ConfigParser
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")

json_lock = Lock()

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "update.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def read_json(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Gagal baca {file_path}: {e}")
        return None

def write_json_lock(file_path, data):
    try:
        with json_lock:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Berhasil tulis {file_path}")
    except Exception as e:
        logging.error(f"Gagal tulis {file_path}: {e}")

def fetch_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Gagal ambil {url}: {e}")
        return None

def push_to_git():
    try:
        repo = Repo(os.path.dirname(__file__))
        repo.git.add(".")
        repo.index.commit("Update data komik")
        origin = repo.remote(name="origin")
        origin.push()
        logging.info("Berhasil push ke GitHub")
    except Exception as e:
        logging.error(f"Gagal push ke GitHub: {e}")

def read_config():
    try:
        config = ConfigParser()
        config.read(CONFIG_PATH)
        return config
    except Exception as e:
        logging.error(f"Gagal baca config.ini: {e}")
        return None

def upload_to_cloudinary(image_url):
    try:
        config = read_config()
        if not config or 'CloudinaryData' not in config:
            logging.error("Cloudinary config nggak ada")
            return None
        response = upload(
            image_url,
            cloud_name=config['CloudinaryData'].get('cloud_name'),
            api_key=config['CloudinaryData'].get('api_key'),
            api_secret=config['CloudinaryData'].get('api_secret')
        )
        url, _ = cloudinary_url(response['public_id'], secure=True)
        logging.info(f"Berhasil upload {image_url}: {url}")
        return url
    except Exception as e:
        logging.error(f"Gagal upload {image_url}: {e}")
        return None

def paraphrase_synopsis(synopsis):
    try:
        replacements = {
            "adalah": "merupakan",
            "yang": "dimana",
            "dengan": "bersama",
            "untuk": "guna",
            "di": "pada"
        }
        paraphrased = synopsis
        for old, new in replacements.items():
            paraphrased = paraphrased.replace(old, new)
        return paraphrased.strip()
    except Exception as e:
        logging.error(f"Gagal paraphrase: {e}")
        return synopsis