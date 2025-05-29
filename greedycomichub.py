import argparse
import requests
import os
import json
import time
import subprocess
import logging
from bs4 import BeautifulSoup
import cloudinary
import cloudinary.uploader
import configparser

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/update.log'),
        logging.StreamHandler()
    ]
)

# Konfigurasi
DATA_DIR = "data"
TEMP_IMAGES_DIR = "temp_images"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://komiku.id/",
    "Accept-Language": "en-US,en;q=0.9"
}
RETRY_LIMIT = 3
DELAY_BETWEEN_REQUESTS = 1

# Konfigurasi Cloudinary dan GitHub dari config.ini
try:
    config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        raise FileNotFoundError("File config.ini tidak ditemukan!")
    config.read('config.ini')
    CLOUDINARY_CLOUD_NAME = config['DEFAULT']['CloudinaryCloudName']
    CLOUDINARY_API_KEY = config['DEFAULT']['CloudinaryApiKey']
    CLOUDINARY_API_SECRET = config['DEFAULT']['CloudinaryApiSecret']
    GITHUB_TOKEN = config['DEFAULT']['GitHubToken']
    GITHUB_REPO = config['DEFAULT']['GitHubRepo']
except Exception as e:
    logging.error(f"Error membaca config.ini: {e}")
    print(f"Error membaca config.ini: {e}")
    exit(1)

# Setup Cloudinary
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

def download_image(url, save_path):
    if os.path.exists(save_path):
        logging.info(f"Gambar sudah ada di {save_path}, lewati download.")
        return True
    logging.info(f"Download {url} ke {save_path}...")
    for attempt in range(RETRY_LIMIT):
        try:
            response = requests.get(url, stream=True, headers=HEADERS, timeout=10)
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

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Buat direktori: {directory}")

def scrape_comic_metadata(comic_url, comic_name):
    logging.info(f"Scrape metadata komik dari {comic_url}...")
    try:
        response = requests.get(comic_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find('h1', class_='title') or soup.find('h1')
        description = soup.find('div', class_='desc') or soup.find('p', class_='desc')
        creator = soup.find('a', rel='tag') or soup.find('span', string=lambda x: 'author' in x.lower() if x else False)
        cover_img = soup.find('div', class_='ims').find('img') if soup.find('div', class_='ims') else None

        title = title.text.strip() if title else comic_name.replace("-", " ").title()
        description = description.text.strip() if description else f"Komik {comic_name.replace('-', ' ').title()} tersedia di GreedyComicHub."
        creator = creator.text.strip() if creator else "Unknown Author"
        cover_url = None

        if cover_img and cover_img.get('src'):
            cover_src = cover_img['src']
            if not cover_src.startswith('http'):
                base_url = comic_url.split('/')[0] + '//' + comic_url.split('/')[2]
                cover_src = base_url + cover_src
            cover_path = os.path.join(TEMP_IMAGES_DIR, f"{comic_name}-cover.jpg")
            ensure_directory(TEMP_IMAGES_DIR)
            if download_image(cover_src, cover_path):
                cover_url = upload_to_cloudinary(cover_path, comic_name, 0, 0)
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
            "title": comic_name.replace("-", " ").title(),
            "author": "Unknown Author",
            "synopsis": f"Komik {comic_name.replace('-', ' ').title()} tersedia di GreedyComicHub.",
            "cover": "",
            "chapters": {}
        }

def scrape_chapter_images(chapter_url, chapter_num):
    logging.info(f"Ambil URL gambar chapter {chapter_num} dari {chapter_url}...")
    image_urls = []
    for attempt in range(RETRY_LIMIT):
        try:
            response = requests.get(chapter_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            image_elements = soup.find_all("img")
            for img in image_elements:
                img_url = img.get("data-full") or img.get("data-src") or img.get("src")
                if img_url and "komiku.id" in img_url and "wp-content/uploads" in img_url:
                    img_url = img_url.split("?")[0]
                    image_urls.append(img_url)
            if image_urls:
                logging.info(f"Berhasil ambil {len(image_urls)} URL gambar untuk chapter {chapter_num}.")
                return image_urls
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            logging.error(f"Error ambil URL gambar (percobaan {attempt + 1}/{RETRY_LIMIT}): {e}")
            time.sleep(DELAY_BETWEEN_REQUESTS)
    logging.error(f"Gagal ambil URL gambar chapter {chapter_num}.")
    return []

def save_comic_data(comic_id, comic_data):
    ensure_directory(DATA_DIR)
    file_path = os.path.join(DATA_DIR, f"{comic_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(comic_data, f, indent=2, ensure_ascii=False)
    logging.info(f"Berhasil simpan data komik ke {file_path}")

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

def push_to_github():
    logging.info("Push perubahan ke GitHub...")
    try:
        subprocess.run(["git", "add", DATA_DIR], check=True)
        subprocess.run(["git", "commit", "-m", "Update comic data"], check=True)
        subprocess.run(["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", "main"], check=True)
        logging.info("Berhasil push ke GitHub.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error saat push ke GitHub: {e}")
        raise

def scrape(comic_url, comic_name):
    comic_id = comic_name.lower().replace(" ", "-")
    comic_data = scrape_comic_metadata(comic_url, comic_id)
    save_comic_data(comic_id, comic_data)
    update_index(comic_id, comic_data)
    push_to_github()

def add_chapter(comic_name, chapter_url, chapter_num):
    comic_id = comic_name.lower().replace(" ", "-")
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if not os.path.exists(comic_file):
        logging.error(f"Komik {comic_name} tidak ditemukan! Tambah komik dulu dengan perintah 'scrape'.")
        return
    with open(comic_file, "r", encoding="utf-8") as f:
        comic_data = json.load(f)

    chapter_num_str = str(chapter_num)
    if chapter_num_str in comic_data["chapters"]:
        logging.error(f"Chapter {chapter_num} untuk {comic_name} sudah ada!")
        return

    image_urls = scrape_chapter_images(chapter_url, chapter_num)
    if not image_urls:
        logging.error(f"Tidak ada gambar untuk chapter {chapter_num}.")
        return

    chapter_pages = []
    chapter_dir = os.path.join(TEMP_IMAGES_DIR, f"{comic_id}/chapter_{chapter_num}")
    ensure_directory(chapter_dir)

    for page, image_url in enumerate(image_urls, 1):
        file_name = f"page{page}.jpg"
        local_path = os.path.join(chapter_dir, file_name)
        if not download_image(image_url, local_path):
            logging.error(f"Gagal download halaman {page}.")
            continue
        cloudinary_url = upload_to_cloudinary(local_path, comic_id, chapter_num, page)
        if cloudinary_url:
            chapter_pages.append(cloudinary_url)
            logging.info(f"Upload halaman {page} ke Cloudinary: {cloudinary_url}")
        else:
            logging.error(f"Gagal upload halaman {page}.")
        os.remove(local_path)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    if not chapter_pages:
        logging.error(f"Tidak ada halaman yang berhasil diupload untuk chapter {chapter_num}.")
        return

    comic_data["chapters"][chapter_num_str] = {
        "pages": chapter_pages
    }
    save_comic_data(comic_id, comic_data)
    update_index(comic_id, comic_data)
    push_to_github()
    logging.info(f"Chapter {chapter_num} untuk {comic_name} berhasil ditambahkan!")

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

def main():
    try:
        parser = argparse.ArgumentParser(description="GreedyComicHub CLI")
        subparsers = parser.add_subparsers(dest='command')

        scrape_parser = subparsers.add_parser('scrape', help='Scrape metadata komik dari URL')
        scrape_parser.add_argument('url', help='URL situs komik')
        scrape_parser.add_argument('comic_name', help='Nama komik')

        chapter_parser = subparsers.add_parser('add-chapter', help='Tambah chapter untuk komik')
        chapter_parser.add_argument('comic_name', help='Nama komik')
        chapter_parser.add_argument('chapter_url', help='URL chapter')
        chapter_parser.add_argument('chapter_num', type=float, help='Nomor chapter')

        subparsers.add_parser('list-comics', help='Tampilkan daftar komik')

        args = parser.parse_args()

        if args.command == 'scrape':
            scrape(args.url, args.comic_name)
        elif args.command == 'add-chapter':
            add_chapter(args.comic_name, args.chapter_url, args.chapter_num)
        elif args.command == 'list-comics':
            list_comics()
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Error in main: {e}")
        exit(1)

if __name__ == "__main__":
    main()