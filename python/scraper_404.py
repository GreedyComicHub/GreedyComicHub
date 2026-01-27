import json
import logging
import os
import subprocess
import time
import requests
from bs4 import BeautifulSoup
from filelock import FileLock
from configparser import ConfigParser

# Setup direktori
DATA_DIR = "data404"
LOG_DIR = "logs"
for directory in [DATA_DIR, LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Setup logging
LOG_FILE = os.path.join(LOG_DIR, "scrape_404.log")
if os.path.exists(LOG_FILE):
    backup_file = os.path.join(LOG_DIR, "scrape_404.log.1")
    if os.path.exists(backup_file):
        os.remove(backup_file)
    os.rename(LOG_FILE, backup_file)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Headers untuk scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://mangapoi.my/"
}

# Load konfigurasi
config = ConfigParser()
config.read("config.ini")
GITHUB_TOKEN = config.get("GitHub", "GitHubToken")
GITHUB_REPO = config.get("GitHub", "GitHubRepo")

def fetch_page(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
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
    promo_phrases = ["baca komik", "bahasa indonesia", "di mangapoi"]
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
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

def write_json(file_path, data):
    lock = FileLock(file_path + ".lock")
    with lock:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

def push_to_github():
    logging.info("Push perubahan ke GitHub...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            logging.info("Tidak ada perubahan. Skip push.")
            return True
        subprocess.run(["git", "commit", "-m", "Update comic data for 404"], check=True)
        subprocess.run(
            ["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", "main"],
            check=True
        )
        logging.info("Berhasil push ke GitHub.")
        return True
    except Exception as e:
        logging.error(f"Error push: {e}")
        return False

def get_comic_id_from_url(url):
    comic_id = url.rstrip("/").split("/")[-1].lower()
    logging.info(f"Nama komik dari URL: ID={comic_id}, Display={comic_id.capitalize()}")
    return comic_id

def scrape_comic(url):
    logging.info(f"Mulai scrape komik: {url}")
    comic_id = get_comic_id_from_url(url)
    index_file = os.path.join(DATA_DIR, "index.json")

    # Fetch halaman
    html = fetch_page(url)
    if not html:
        logging.error(f"Gagal ambil halaman {url}")
        return

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Ambil metadata
        title = soup.find('h2').text.strip() if soup.find('h2') else "Unknown Title"
        cover_url = soup.find('img', alt=title)
        cover_url = cover_url['src'] if cover_url and cover_url['src'].startswith('http') else "placeholder.jpg"
        author = soup.find('li', string=lambda x: x and 'Author' in x)
        author = author.find('span').text.strip() if author else "Unknown Author"
        synopsis = soup.find('div', class_='series-synops')
        synopsis = synopsis.find('p').text.strip() if synopsis and synopsis.find('p') else "No synopsis available."
        synopsis = paraphrase_synopsis(synopsis)
        chapter_list = soup.find('ul', class_='series-chapterlist')
        total_chapters = len(chapter_list.find_all('li')) if chapter_list else 0

        # Buat data untuk index.json
        comic_data = {
            "title": title,
            "author": author,
            "synopsis": synopsis,
            "cover": cover_url,
            "total_chapters": total_chapters,
            "source_url": url,
            "type": "404 Not Found"
        }

        # Update index.json
        index_data = read_json(index_file)
        index_data[comic_id] = comic_data
        write_json(index_file, index_data)
        logging.info(f"Berhasil update {comic_id} di {index_file}")

    except Exception as e:
        logging.error(f"Error scrape komik {url}: {e}")

def main():
    # List URL komik (ganti dengan URL yang mau discrap)
    comic_urls = [
        "https://mangapoi.my/im-the-only-man-on-the-military-base/",
        # Tambah URL lain di sini
    ]
    for url in comic_urls:
        scrape_comic(url)
    push_to_github()

if __name__ == "__main__":
    main()