import argparse
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin

# Cek dependency
try:
    import cloudinary
    import cloudinary.uploader
    import requests
    from bs4 import BeautifulSoup
    from configparser import ConfigParser
except ImportError as e:
    print(f"Error: Library hilang - {e}")
    print("Pastikan semua library terinstall: pip install cloudinary requests beautifulsoup4")
    exit(1)

# Setup logging (ke file dan console)
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Log rotation: backup log lama, reset log baru
LOG_FILE = os.path.join(LOG_DIR, "update.log")
if os.path.exists(LOG_FILE):
    backup_file = os.path.join(LOG_DIR, "update.log.1")
    if os.path.exists(backup_file):
        os.remove(backup_file)
    os.rename(LOG_FILE, backup_file)

# Logger dengan dua handler: file dan console
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Handler untuk file
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler untuk console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Direktori data
DATA_DIR = "data"
TEMP_IMAGES_DIR = "temp_images"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(TEMP_IMAGES_DIR):
    os.makedirs(TEMP_IMAGES_DIR)

# Load konfigurasi dari config.ini
try:
    config = ConfigParser()
    config.read("config.ini")
    CLOUDINARY_CLOUD_NAME = config.get("Cloudinary", "CloudName")
    CLOUDINARY_API_KEY = config.get("Cloudinary", "ApiKey")
    CLOUDINARY_API_SECRET = config.get("Cloudinary", "ApiSecret")
    GITHUB_TOKEN = config.get("GitHub", "GitHubToken")
    GITHUB_REPO = config.get("GitHub", "GitHubRepo")
except Exception as e:
    logging.error(f"Gagal membaca config.ini: {e}")
    exit(1)

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)
logging.info(f"Menggunakan akun Cloudinary: {CLOUDINARY_CLOUD_NAME}")

# Header untuk request agar mirip browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://komiku.org/"
}

BASE_URL = "https://komiku.org"

def get_comic_id_and_display_name(url):
    """Ambil ID komik dan nama display dari URL."""
    path = urlparse(url).path
    comic_id = path.split("/")[-2] if path.endswith("/") else path.split("/")[-1]
    comic_id = comic_id.replace("manga-", "").replace("/", "")
    display_name = " ".join(word.capitalize() for word in comic_id.split("-"))
    logging.info(f"Nama komik dari URL: ID={comic_id}, Display={display_name}")
    return comic_id, display_name

def fetch_page(url, retries=3, delay=2):
    """Ambil halaman web dengan retry jika gagal."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.warning(f"Gagal mengambil {url} (percobaan {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logging.error(f"Tidak bisa mengambil {url} setelah {retries} percobaan.")
                return None
    return None

def paraphrase_synopsis(original_synopsis):
    """Parafrase sinopsis biar beda kalimat tapi makna sama."""
    if not original_synopsis or original_synopsis == "No synopsis available.":
        return "Petualangan epik di dunia fantasi yang penuh dengan sihir dan misteri."

    # Dictionary untuk mapping kata/phrase biar lebih variatif
    phrase_map = {
        "perjalanan": ["petualangan", "kisah", "cerita"],
        "sihir": ["magis", "kekuatan ajaib", "ilmu sihir"],
        "kekuasaan": ["ambisi", "dominasi", "kuasa"],
        "intrik politik": ["konspirasi politik", "persaingan politik", "intrik kekuasaan"],
        "fantasi": ["dunia imajiner", "alam fantasi", "dunia ajaib"],
        "menghadapi": ["melawan", "berhadapan dengan", "menantang"]
    }

    # Split kalimat jadi kata-kata
    words = original_synopsis.lower().split()
    paraphrased = []
    for word in words:
        # Ganti kata/phrase kalo ada di mapping
        new_word = phrase_map.get(word, word)
        if isinstance(new_word, list):
            new_word = new_word[0]  # Ambil variasi pertama
        paraphrased.append(new_word)

    # Gabungkan kata-kata jadi kalimat
    new_synopsis = " ".join(paraphrased).capitalize()

    # Tambah variasi kalimat
    if "perjalanan" in original_synopsis.lower() or "petualangan" in new_synopsis.lower():
        new_synopsis = f"Seorang penyihir legendaris memulai {new_synopsis} yang mendebarkan."
    elif "intrik" in original_synopsis.lower() or "konspirasi" in new_synopsis.lower():
        new_synopsis = f"{new_synopsis} di tengah dunia yang penuh dengan rahasia dan bahaya."

    logging.info(f"Sinopsis asli: {original_synopsis}")
    logging.info(f"Sinopsis setelah parafrase: {new_synopsis}")
    return new_synopsis

def scrape_comic_details(url):
    """Scrape detail komik dari halaman utama."""
    html = fetch_page(url)
    if not html:
        return None, None, None, None, None, None

    soup = BeautifulSoup(html, "html.parser")
    
    # Ambil judul
    title_element = soup.find("h1")
    title = title_element.text.strip() if title_element else "Unknown Title"
    logging.info(f"Nama komik dari <h1>: {title}")

    # Ambil author
    author = "Unknown Author"
    # Pendekatan 1: Cari span yang berisi "Author"
    author_element = soup.find("span", string=lambda text: "Author" in text if text else False)
    if author_element:
        author = author_element.find_next("span").text.strip() if author_element.find_next("span") else "Unknown Author"
    else:
        # Pendekatan 2: Cari di tabel info komik
        info_table = soup.find("table", class_="info-komik")
        if info_table:
            author_row = info_table.find("td", string=lambda text: "Author" in text if text else False)
            if author_row:
                author = author_row.find_next("td").text.strip() if author_row.find_next("td") else "Unknown Author"
    logging.info(f"Author ditemukan: {author}")

    # Ambil genre
    genre = "Fantasy"  # Default
    genre_element = soup.find("span", string=lambda text: "Genre" in text if text else False)
    if genre_element:
        genre = genre_element.find_next("span").text.strip() if genre_element.find_next("span") else "Fantasy"
    else:
        # Pendekatan 2: Cari di tabel info komik
        if info_table:
            genre_row = info_table.find("td", string=lambda text: "Genre" in text if text else False)
            if genre_row:
                genre = genre_row.find_next("td").text.strip() if genre_row.find_next("td") else "Fantasy"
    logging.info(f"Genre ditemukan: {genre}")

    # Ambil sinopsis
    synopsis = "No synopsis available."
    synopsis_element = soup.find("div", class_="desc")
    if synopsis_element:
        synopsis = synopsis_element.text.strip()
    else:
        # Fallback: Cari di meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            synopsis = meta_desc["content"].strip()
    
    # Parafrase sinopsis
    synopsis = paraphrase_synopsis(synopsis)

    # Ambil cover
    cover_url = None
    cover_selectors = [
        'meta[property="og:image"]',
        'meta[itemprop="image"]',
        'img[itemprop="image"]'
    ]
    for selector in cover_selectors:
        cover_element = soup.select_one(selector)
        if cover_element and cover_element.get("content"):
            cover_url = cover_element["content"]
            break
        elif cover_element and cover_element.get("src"):
            cover_url = cover_element["src"]
            break
    if not cover_url:
        logging.warning("Cover image tidak ditemukan.")
        cover_url = ""

    return title, author, synopsis, cover_url, soup, genre

def scrape_chapter_list(url, soup):
    """Scrape daftar chapter dari halaman utama komik."""
    chapters = {}
    logging.info(f"Mencari daftar chapter dari {url}...")

    chapter_elements = soup.select("td.judulseries a")
    logging.info(f"Ditemukan {len(chapter_elements)} elemen td.judulseries")

    if not chapter_elements:
        logging.warning("Tidak ditemukan chapter. Mencoba fallback...")
        all_links = soup.select("a[href*='chapter']")
        for link in all_links:
            href = link.get("href", "")
            if "chapter" in href.lower():
                chapter_num = href.split("chapter-")[-1].split("/")[0].split("-")[0]
                try:
                    chapter_num = int(chapter_num)
                    chapters[chapter_num] = href
                    logging.info(f"Chapter {chapter_num} ditemukan via fallback: {href}")
                except ValueError:
                    continue

    for element in chapter_elements:
        href = element.get("href", "")
        chapter_text = element.text.lower()
        if "chapter" in chapter_text:
            chapter_num = chapter_text.split("chapter")[-1].strip().split("-")[0]
            try:
                chapter_num = int(chapter_num)
                chapters[chapter_num] = href
                logging.info(f"Chapter {chapter_num}: {href}")
            except ValueError:
                logging.warning(f"Chapter tidak valid: {chapter_text}")
                continue

    return chapters

def scrape_chapter_images(chapter_url):
    """Scrape URL gambar dari halaman chapter."""
    full_url = urljoin(BASE_URL, chapter_url)
    html = fetch_page(full_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    
    title_element = soup.find("h1")
    chapter_title = title_element.text.strip() if title_element else "Unknown Chapter"
    logging.info(f"Judul chapter: {chapter_title}")

    image_urls = []
    selectors = [
        'img[itemprop="image"]',
        '#readerarea img',
        'div.komik img',
        'img[src*="img.komiku.org"]'
    ]

    for selector in selectors:
        image_elements = soup.select(selector)
        logging.info(f"Ditemukan {len(image_elements)} gambar dengan {selector}")
        if image_elements:
            for img in image_elements:
                src = img.get("src", "")
                if src and src.startswith("http"):
                    image_urls.append(src)
            break

    if not image_urls:
        logging.error(f"Tidak ada gambar untuk chapter ini: {chapter_url}")
        return []

    return image_urls

def upload_to_cloudinary(image_url, comic_id, chapter_num):
    """Upload gambar ke Cloudinary dan kembalikan URL publik."""
    try:
        response = requests.get(image_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        image_name = image_url.split("/")[-1]
        temp_path = os.path.join(TEMP_IMAGES_DIR, image_name)
        with open(temp_path, "wb") as f:
            f.write(response.content)

        folder = f"greedycomichub/{comic_id}/chapter_{chapter_num}"
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
        logging.error(f"Gagal upload gambar {image_url} ke Cloudinary: {e}")
        return image_url

def update_comic(url, start_chapter, end_chapter):
    """Update data komik dengan chapter tertentu."""
    start_time = time.time()
    logging.info(f"Mulai update komik: {url}")

    comic_id, display_name = get_comic_id_and_display_name(url)
    title, author, synopsis, cover_url, soup, genre = scrape_comic_details(url)
    if not title:
        logging.error("Gagal mendapatkan detail komik. Proses dihentikan.")
        return

    chapters = scrape_chapter_list(url, soup)
    if not chapters:
        logging.error("Tidak ada chapter yang ditemukan. Proses dihentikan.")
        return

    # Pastiin semua field ada
    comic_data = {
        "title": title if title else "Unknown Title",
        "author": author if author else "Unknown Author",
        "synopsis": synopsis if synopsis else "No synopsis available.",
        "cover": cover_url if cover_url else "",
        "genre": genre if genre else "Fantasy",
        "chapters": {}
    }

    # Log semua field buat debug
    logging.info(f"Comic Data sebelum load file lama: {json.dumps(comic_data, indent=2)}")

    # Load data komik yang sudah ada
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if os.path.exists(comic_file):
        with open(comic_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            # Pastiin semua field ada, kalo nggak ada di file lama, ambil dari data baru
            comic_data["title"] = existing_data.get("title", comic_data["title"])
            comic_data["author"] = existing_data.get("author", comic_data["author"])
            comic_data["synopsis"] = existing_data.get("synopsis", comic_data["synopsis"])
            comic_data["cover"] = existing_data.get("cover", comic_data["cover"])
            comic_data["genre"] = existing_data.get("genre", comic_data["genre"])
            comic_data["chapters"] = existing_data.get("chapters", {})
        logging.info(f"Loaded existing comic data from {comic_file}")

    # Update chapter yang diminta
    first_image_url = None
    for chapter_num in range(start_chapter, end_chapter + 1):
        if chapter_num in chapters:
            logging.info(f"Chapter {chapter_num} ditemukan dengan kunci {chapter_num}: {chapters[chapter_num]}")
            logging.info(f"Ambil URL gambar chapter {chapter_num} dari {chapters[chapter_num]}...")
            image_urls = scrape_chapter_images(chapters[chapter_num])
            if not image_urls:
                logging.warning(f"Chapter {chapter_num} dilewati karena tidak ada gambar.")
                continue

            uploaded_urls = []
            for idx, img_url in enumerate(image_urls, 1):
                logging.info(f"Upload gambar {idx}/{len(image_urls)} untuk chapter {chapter_num}...")
                uploaded_url = upload_to_cloudinary(img_url, comic_id, chapter_num)
                uploaded_urls.append(uploaded_url)
                # Simpen gambar pertama buat cover
                if not first_image_url:
                    first_image_url = uploaded_url

            comic_data["chapters"][str(chapter_num)] = {
                "pages": uploaded_urls  # Format lama
            }

    # Kalo cover dari Komiku gagal, ganti pake gambar pertama dari chapter
    if first_image_url and (not comic_data["cover"] or fetch_page(comic_data["cover"]) is None):
        logging.info(f"Cover asli gagal load, ganti dengan gambar pertama: {first_image_url}")
        comic_data["cover"] = first_image_url

    # Log comic_data sebelum disimpan
    logging.info(f"Comic Data sebelum disimpan: {json.dumps(comic_data, indent=2)}")

    # Simpan data komik
    with open(comic_file, "w", encoding="utf-8") as f:
        json.dump(comic_data, f, indent=4)
    logging.info(f"Berhasil simpan data komik ke {comic_file}")

    # Update indeks
    update_index(comic_id, comic_data)

    # Log waktu eksekusi
    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"Update selesai dalam {execution_time:.2f} detik.")

def update_index(comic_id, comic_data):
    """Update file indeks dengan daftar komik."""
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = {}

    # Load index.json, handle jika format salah
    if os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            # Pastikan index_data adalah dict
            if not isinstance(index_data, dict):
                logging.warning(f"Format index.json salah: {index_data}. Reset ke dict kosong.")
                index_data = {}
        except Exception as e:
            logging.error(f"Gagal membaca index.json: {e}. Reset ke dict kosong.")
            index_data = {}
    else:
        logging.info("index.json tidak ditemukan. Membuat baru.")

    # Perbarui atau tambah entri komik (format lama, tanpa author)
    comic_entry = {
        "title": comic_data["title"],
        "synopsis": comic_data["synopsis"],
        "cover": comic_data["cover"],
        "total_chapters": len(comic_data["chapters"])
    }
    index_data[comic_id] = comic_entry

    # Log index_data sebelum disimpan
    logging.info(f"Index Data sebelum disimpan: {json.dumps(index_data, indent=2)}")

    # Simpan index.json
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=4)
    logging.info(f"Berhasil update indeks di {index_file}")

def push_to_github():
    """Push perubahan ke GitHub."""
    logging.info("Push perubahan ke GitHub...")
    try:
        data_path = os.path.abspath(DATA_DIR)
        logging.info(f"Menambahkan file di {data_path} ke Git...")
        
        result_add = subprocess.run(["git", "add", data_path], capture_output=True, text=True)
        logging.info(f"Git add output: {result_add.stdout}{result_add.stderr}")

        result_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        logging.info(f"Git status output: {result_status.stdout}{result_status.stderr}")
        if not result_status.stdout.strip():
            logging.info("Tidak ada perubahan baru. Skipping commit and push.")
            return True

        result_commit = subprocess.run(
            ["git", "commit", "-m", "Update comic data"],
            capture_output=True, text=True
        )
        logging.info(f"Git commit output: {result_commit.stdout}{result_commit.stderr}")
        if result_commit.returncode != 0:
            logging.error("Gagal commit perubahan.")
            return False

        result_push = subprocess.run(
            ["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", "main"],
            capture_output=True, text=True
        )
        logging.info(f"Git push output: {result_push.stdout}{result_push.stderr}")
        if result_push.returncode != 0:
            logging.error("Gagal push perubahan ke GitHub.")
            return False

        logging.info("Berhasil push perubahan ke GitHub.")
        return True
    except Exception as e:
        logging.error(f"Error saat push ke GitHub: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="GreedyComicHub Scraper")
    subparsers = parser.add_subparsers(dest="command")

    parser_update = subparsers.add_parser("update", help="Update data komik")
    parser_update.add_argument("url", help="URL halaman komik")
    parser_update.add_argument("--start", type=int, default=1, help="Chapter awal")
    parser_update.add_argument("--end", type=int, default=1, help="Chapter akhir")

    args = parser.parse_args()

    if args.command == "update":
        update_comic(args.url, args.start, args.end)
        push_to_github()
        logging.info(f"Update Komik {args.url} selesai.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()