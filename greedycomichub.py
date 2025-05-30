"""
GreedyComicHub: Scrape komik dari komiku.org (atau situs lain), simpen gambar ke Cloudinary, dan update website via GitHub.
Struktur:
- Scrape metadata (judul, author), daftar chapter, gambar.
- Simpan JSON (data/<comic>.json, data/index.json) untuk website (index.html, comic.html, chapter.html).
- Upload gambar ke Cloudinary, push JSON ke GitHub.
Output: JSON dibaca website via JS (key: data.chapters[chapter].pages).
Cara pakai:
- python greedycomichub.py update <URL> --start X --end Y
- python greedycomichub.py list-comics
- python greedycomichub.py commands
Modifikasi:
- Tambah situs baru: Update SITE_CONFIG (line 50). Cari tag di Ctrl+U.
- Ubah layout website: Cek JS di website yang baca JSON (data.chapters).
- Error: Kirim Python, HTML/JS, JSON, console error ke Grok.
- Hapus komik: Hapus data/<comic>.json, edit data/index.json, commit ke GitHub.
"""

import argparse
import requests
import os
import json
import time
import subprocess
import logging
import re
from bs4 import BeautifulSoup
import cloudinary
import cloudinary.uploader
import configparser
import urllib3

# Nonaktifkan peringatan SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lines 30-50: Konfigurasi situs (komiku.org).
# Tambah situs baru: Copy format, ganti base_url, chapter_selector, image_selector.
# Cari tag di Ctrl+U (chapter di halaman komik, gambar di halaman chapter).
# Contoh: Kalau domain berubah (e.g., komik.id ke komiku.org), ganti base_url.
SITE_CONFIG = {
    'komiku': {
        'base_url': 'https://komiku.org',
        'chapter_selector': 'td.judulseries',
        'image_selector': 'img[itemprop="image"]'
    }
}

# Lines 50-70: Setup logging dan direktori.
# Logging ke logs/update.log untuk debugging.
# Direktori data/ untuk JSON, temp_images/ untuk gambar sementara.
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Lines 70-90: Konfigurasi global.
# BASE_URL diambil dari SITE_CONFIG berdasarkan URL.
# HEADERS untuk HTTP request, RETRY_LIMIT dan DELAY untuk error handling.
DATA_DIR = "data"
TEMP_IMAGES_DIR = "temp_images"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://komiku.org/",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}
RETRY_LIMIT = 3
DELAY_BETWEEN_REQUESTS = 2

# Lines 90-120: Baca config.ini untuk Cloudinary dan GitHub.
# Error kalau config.ini hilang atau salah.
try:
    config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        raise FileNotFoundError("File config.ini tidak ditemukan!")
    config.read('config.ini', encoding='utf-8')
    CLOUDINARY_CLOUD_NAME = config['DEFAULT']['CloudinaryCloudName']
    CLOUDINARY_API_KEY = config['DEFAULT']['CloudinaryApiKey']
    CLOUDINARY_API_SECRET = config['DEFAULT']['CloudinaryApiSecret']
    GITHUB_TOKEN = config['DEFAULT']['GitHubToken']
    GITHUB_REPO = config['DEFAULT']['GitHubRepo']
except Exception as e:
    logging.error(f"Error membaca config.ini: {e}")
    print(f"Error membaca config.ini: {e}")
    exit(1)

# Lines 120-140: Setup Cloudinary.
# Error kalau setup gagal (e.g., API key salah).
try:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )
    logging.info(f"Menggunakan akun Cloudinary: {CLOUDINARY_CLOUD_NAME}")
except Exception as e:
    logging.error(f"Error setup Cloudinary: {e}")
    print(f"Error setup Cloudinary: {e}")
    exit(1)

# Lines 140-170: Upload gambar ke Cloudinary.
# Public ID: greedycomichub/<comic_id>/chapter_X/page_Y.
# Retry kalau gagal, return URL Cloudinary.
def upload_to_cloudinary(file_path, comic_id, chapter_num, page_num):
    public_id = f"greedycomichub/{comic_id}/chapter_{chapter_num}/page_{page_num}"
    for attempt in range(RETRY_LIMIT):
        try:
            response = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            logging.info(f"Berhasil upload ke Cloudinary: {response['secure_url']}")
            return response["secure_url"]
        except Exception as e:
            logging.error(f"Error upload ke Cloudinary (percobaan {attempt + 1}/{RETRY_LIMIT}): {e}")
            time.sleep(DELAY_BETWEEN_REQUESTS)
    logging.error(f"Gagal upload ke Cloudinary setelah {RETRY_LIMIT} percobaan.")
    return None

# Lines 170-200: Download gambar dari URL.
# Simpan ke save_path, skip kalau sudah ada.
# Retry kalau gagal, return True/False.
def download_image(url, save_path):
    if os.path.exists(save_path):
        logging.info(f"Gambar sudah ada di {save_path}, lewati download.")
        return True
    logging.info(f"Download {url} ke {save_path}...")
    for attempt in range(RETRY_LIMIT):
        try:
            response = requests.get(url, stream=True, headers=HEADERS, timeout=10, verify=False)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logging.info(f"Berhasil download {url}")
            return True
        except Exception as e:
            logging.error(f"Error download (percobaan {attempt + 1}/{RETRY_LIMIT}): {e}")
            time.sleep(DELAY_BETWEEN_REQUESTS)
    logging.error(f"Gagal download {url}.")
    return False

# Lines 200-210: Buat direktori kalau belum ada.
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Buat direktori: {directory}")

# Lines 210-250: Ambil nama komik dari URL.
# Slug (e.g., magic-emperor) jadi ID, format rapi (Magic Emperor) untuk display.
# Fallback: Scrape <h1 class='title'>.
def get_comic_name_from_url(url):
    try:
        slug = url.rstrip('/').split('/')[-1]
        comic_id = slug.lower().replace(' ', '-')
        display_name = ' '.join(word.capitalize() for word in slug.split('-'))
        logging.info(f"Nama komik dari URL: ID={comic_id}, Display={display_name}")
        
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find('h1', class_='title') or soup.find('h1')
        if title and title.text.strip():
            display_name = title.text.strip()
            logging.info(f"Nama komik dari <h1>: {display_name}")
        
        return comic_id, display_name
    except Exception as e:
        logging.error(f"Error ambil nama komik: {e}")
        return slug, slug.replace('-', ' ').title()

# Lines 250-300: Scrape metadata komik (judul, author, synopsis, cover).
# Simpan cover ke Cloudinary, return dict untuk JSON.
def scrape_comic_metadata(comic_url, comic_id, display_name):
    logging.info(f"Scrape metadata komik dari {comic_url}...")
    try:
        response = requests.get(comic_url, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find('h1', class_='title') or soup.find('h1')
        description = soup.find('div', class_='desc') or soup.find('p', class_='desc')
        creator = soup.find('a', rel='tag') or soup.find('span', string=lambda x: 'author' in x.lower() if x else False)
        cover_img = soup.find('div', class_='ims').find('img') if soup.find('div', class_='ims') else None

        title = title.text.strip() if title else display_name
        description = description.text.strip() if description else f"Komik {display_name} tersedia di GreedyComicHub."
        creator = creator.text.strip() if creator else "Unknown Author"
        cover_url = None

        if cover_img and cover_img.get('src'):
            cover_src = cover_img['src']
            if not cover_src.startswith('http'):
                cover_src = SITE_CONFIG['komiku']['base_url'] + cover_src
            cover_path = os.path.join(TEMP_IMAGES_DIR, f"{comic_id}-cover.jpg")
            ensure_directory(TEMP_IMAGES_DIR)
            if download_image(cover_src, cover_path):
                cover_url = upload_to_cloudinary(cover_path, comic_id, 0, 0)
                if cover_url:
                    logging.info(f"Berhasil upload cover: {cover_url}")
                os.remove(cover_path)

        return {
            "title": title,
            "author": creator,
            "synopsis": description,
            "cover": cover_url or "",
            "chapters": {}
        }
    except Exception as e:
        logging.error(f"Error scrape metadata: {e}")
        return {
            "title": display_name,
            "author": "Unknown Author",
            "synopsis": f"Komik {display_name} tersedia di GreedyComicHub.",
            "cover": "",
            "chapters": {}
        }

# Lines 300-350: Ambil daftar chapter dari halaman komik.
# Cari <td class='judulseries'> (komiku.org).
# Untuk situs baru, ganti selector di line 320 (cari di Ctrl+U).
def get_comic_id_and_chapter_urls(comic_url):
    logging.info(f"Mencari daftar chapter dari {comic_url}...")
    chapter_urls = {}
    try:
        response = requests.get(comic_url, headers=HEADERS, timeout=15, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        chapter_list = soup.find_all(SITE_CONFIG['komiku']['chapter_selector'])
        logging.info(f"Ditemukan {len(chapter_list)} elemen {SITE_CONFIG['komiku']['chapter_selector']}")

        for td in chapter_list:
            link = td.find('a', href=True)
            if link:
                href = link['href']
                chapter_num_match = re.search(r'chapter-(\d+)', href, re.IGNORECASE)
                if chapter_num_match:
                    chapter_num = str(int(chapter_num_match.group(1)))
                    full_url = href if href.startswith('http') else SITE_CONFIG['komiku']['base_url'] + href
                    chapter_urls[chapter_num] = full_url
                    logging.info(f"Chapter {chapter_num} ditambahkan: {full_url}")

        if not chapter_urls:
            logging.warning("Tidak ditemukan chapter. Mencoba fallback...")
            comic_slug = comic_url.split('/')[-2]
            for chapter_num in range(1, 10):
                chapter_url = f"{SITE_CONFIG['komiku']['base_url']}/{comic_slug}-chapter-{chapter_num:02d}/"
                try:
                    response = requests.head(chapter_url, headers=HEADERS, timeout=5, verify=False)
                    if response.status_code == 200:
                        chapter_urls[str(chapter_num)] = chapter_url
                        logging.info(f"Chapter {chapter_num} ditemukan via fallback: {chapter_url}")
                except:
                    continue

        return chapter_urls
    except Exception as e:
        logging.error(f"Error mencari chapter: {e}")
        return {}

# Lines 350-400: Scrape URL gambar dari halaman chapter.
# Cari <img itemprop='image'> (komiku.org).
# Untuk situs baru, ganti selector di line 360 (cari <img> di Ctrl+U).
def scrape_chapter_images(chapter_url, chapter_num, comic_id):
    logging.info(f"Ambil URL gambar chapter {chapter_num} dari {chapter_url}...")
    image_urls = []
    
    try:
        response = requests.get(chapter_url, headers=HEADERS, timeout=15, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        baca_komik = soup.find('div', id='Baca_Komik')
        if baca_komik:
            h2 = baca_komik.find('h2')
            if h2 and h2.text:
                chapter_title = h2.text.strip()
                logging.info(f"Judul chapter: {chapter_title}")
                if f"Chapter {chapter_num}" not in chapter_title and str(int(chapter_num)) not in chapter_title:
                    logging.warning(f"Chapter {chapter_num} tidak cocok dengan judul: {chapter_title}")

        images = soup.find_all(SITE_CONFIG['komiku']['image_selector'])
        logging.info(f"Ditemukan {len(images)} gambar dengan {SITE_CONFIG['komiku']['image_selector']}")

        for img in images:
            src = img.get('src')
            if src and src.startswith('http') and src.endswith('.jpg'):
                image_urls.append(src)
                logging.info(f"URL gambar ditambahkan: {src}")

        return image_urls
    except Exception as e:
        logging.error(f"Error mengakses {chapter_url}: {e}")
        return []

# Lines 400-420: Simpan data komik ke JSON.
# File: data/<comic_id>.json.
def save_comic_data(comic_id, comic_data):
    ensure_directory(DATA_DIR)
    file_path = os.path.join(DATA_DIR, f"{comic_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(comic_data, f, indent=2, ensure_ascii=False)
    logging.info(f"Berhasil simpan data komik ke {file_path}")

# Lines 420-450: Update index.json untuk daftar komik.
# File: data/index.json.
def update_index(comic_id, comic_data):
    ensure_directory(DATA_DIR)
    index_file = os.path.join(DATA_DIR, "index.json")
    index = {}
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)

    comic_summary = {
        "title": comic_data["title"],
        "author": comic_data["author"],
        "synopsis": comic_data["synopsis"],
        "cover": comic_data["cover"],
        "total_chapters": len(comic_data["chapters"])
    }
    index[comic_id] = comic_summary

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    logging.info(f"Berhasil update indeks di {index_file}")

# Lines 450-500: Push perubahan ke GitHub.
# Commit data/, push ke main.
def push_to_github():
    logging.info("Push perubahan ke GitHub...")
    try:
        result_add = subprocess.run(["git", "add", DATA_DIR], capture_output=True, text=True)
        logging.info(f"Git add output: {result_add.stdout}")

        result_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        logging.info(f"Git status output: {result_status.stdout}")

        if not result_status.stdout.strip():
            logging.info("Tidak ada perubahan baru. Skipping commit and push.")
            return True

        result_commit = subprocess.run(["git", "commit", "-m", "Update comic data"], capture_output=True, text=True)
        logging.info(f"Git commit output: {result_commit.stdout}")
        if result_commit.returncode != 0:
            logging.info("Tidak ada perubahan untuk di-commit. Skipping push.")
            return True

        result_push = subprocess.run(
            ["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", "main"],
            capture_output=True, text=True
        )
        logging.info(f"Git push output: {result_push.stdout}")
        if result_push.returncode == 0:
            logging.info("Berhasil push ke GitHub.")
            return True
        else:
            logging.error(f"Error saat push: {result_push.stderr}")
            raise subprocess.CalledProcessError(result_push.returncode, result_push.args, result_push.stdout, result_push.stderr)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error saat push ke GitHub: {e}")
        logging.error(f"Error output: {e.stderr}")
        raise

# Lines 500-600: Update komik dari URL.
# Scrape metadata, chapter, gambar, simpan JSON, push ke GitHub.
# JSON dibaca website (index.html, comic.html, chapter.html).
def update_comic(comic_url, start_chapter, end_chapter):
    comic_id, display_name = get_comic_name_from_url(comic_url)
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    comic_data = {}

    if os.path.exists(comic_file):
        with open(comic_file, "r", encoding="utf-8") as f:
            comic_data = json.load(f)
    else:
        comic_data = scrape_comic_metadata(comic_url, comic_id, display_name)

    chapter_urls = get_comic_id_and_chapter_urls(comic_url)
    if not chapter_urls:
        logging.error("Tidak ditemukan chapter. Proses dihentikan.")
        return

    for chapter_num in range(int(start_chapter), int(end_chapter) + 1):
        chapter_num_str = str(chapter_num)
        chapter_num_padded = f"{chapter_num:02d}"
        chapter_url = None

        for key in [chapter_num_str, chapter_num_padded]:
            if key in chapter_urls:
                chapter_url = chapter_urls[key]
                logging.info(f"Chapter {chapter_num} ditemukan dengan kunci {key}: {chapter_url}")
                break

        if not chapter_url:
            logging.error(f"Chapter {chapter_num} tidak ditemukan. Lewati.")
            continue

        if chapter_num_str in comic_data["chapters"]:
            logging.info(f"Chapter {chapter_num} untuk {comic_id} sudah ada, lewati.")
            continue

        image_urls = scrape_chapter_images(chapter_url, chapter_num, comic_id)
        if not image_urls:
            logging.error(f"Tidak ada gambar untuk chapter {chapter_num}. Lewati.")
            continue

        chapter_pages = []
        chapter_dir = os.path.join(TEMP_IMAGES_DIR, f"{comic_id}/chapter_{chapter_num}")
        ensure_directory(chapter_dir)

        for page, image_url in enumerate(image_urls, 1):
            file_name = f"page{page}.jpg"
            local_path = os.path.join(chapter_dir, file_name)
            if download_image(image_url, local_path):
                cloudinary_url = upload_to_cloudinary(local_path, comic_id, chapter_num, page)
                if cloudinary_url:
                    chapter_pages.append(cloudinary_url)
                    logging.info(f"Upload halaman {page} ke Cloudinary: {cloudinary_url}")
                os.remove(local_path)
            time.sleep(DELAY_BETWEEN_REQUESTS)

        if chapter_pages:
            comic_data["chapters"][chapter_num_str] = {"pages": chapter_pages}
            logging.info(f"Chapter {chapter_num} untuk {comic_id} berhasil ditambahkan!")

    save_comic_data(comic_id, comic_data)
    update_index(comic_id, comic_data)
    if push_to_github():
        logging.info(f"Update {display_name} selesai.")

# Lines 600-620: Tampilkan daftar komik dari index.json.
def list_comics():
    index_file = os.path.join(DATA_DIR, "index.json")
    if not os.path.exists(index_file):
        logging.info("Belum ada komik!")
        return
    with open(index_file, "r", encoding="utf-8") as f:
        index = json.load(f)
    logging.info("Daftar Komik:")
    for comic_id, data in index.items():
        logging.info(f"- {data['title']} ({comic_id})")

# Lines 620-650: Tampilkan daftar command.
def list_commands():
    commands = [
        "update <URL> --start X --end Y: Scrape komik dari URL, ambil chapter X sampai Y, upload gambar, dan update website.",
        "list-comics: Tampilkan daftar komik yang sudah di-scrape.",
        "commands: Tampilkan daftar command ini."
    ]
    print("Available commands:")
    for cmd in commands:
        print(f"- {cmd}")
    logging.info("Daftar command ditampilkan.")

# Lines 650-700: Main function, parse command line.
# Script ini nggak nyentuh layout website (HTML/CSS/JS).
# Kalau website error, cek JS yang baca JSON (data.chapters).
def main():
    try:
        parser = argparse.ArgumentParser(description="GreedyComicHub CLI untuk komiku.org")
        subparsers = parser.add_subparsers(dest='command')

        update_parser = subparsers.add_parser('update', help='Update komik dari URL')
        update_parser.add_argument('url', help='URL komik (e.g., https://komiku.org/manga/magic-emperor/)')
        update_parser.add_argument('--start', type=int, required=True, help='Chapter awal (e.g., 1)')
        update_parser.add_argument('--end', type=int, required=True, help='Chapter akhir (e.g., 2)')

        subparsers.add_parser('list-comics', help='Tampilkan daftar komik')
        subparsers.add_parser('commands', help='Tampilkan daftar command')

        args = parser.parse_args()

        if args.command == 'update':
            update_comic(args.url, args.start, args.end)
        elif args.command == 'list-comics':
            list_comics()
        elif args.command == 'commands':
            list_commands()
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Error in main: {e}")
        exit(1)

if __name__ == "__main__":
    main()