import argparse
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re

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

# Setup logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

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

# List untuk nyimpen error selama proses (hanya level ERROR)
error_summary = []

# Direktori data
DATA_DIR = "data"
TEMP_IMAGES_DIR = "temp_images"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(TEMP_IMAGES_DIR):
    os.makedirs(TEMP_IMAGES_DIR)

# Load konfigurasi
try:
    config = ConfigParser()
    config.read("config.ini")
    CLOUDINARY_CLOUD_NAME = config.get("Cloudinary", "CloudName")
    CLOUDINARY_API_KEY = config.get("Cloudinary", "ApiKey")
    CLOUDINARY_API_SECRET = config.get("Cloudinary", "ApiSecret")
    GITHUB_TOKEN = config.get("GitHub", "GitHubToken")
    GITHUB_REPO = config.get("GitHub", "GitHubRepo")
except Exception as e:
    error_msg = f"Gagal membaca config.ini: {e}"
    logging.error(error_msg)
    error_summary.append(error_msg)
    exit(1)

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)
logging.info(f"Menggunakan akun Cloudinary: {CLOUDINARY_CLOUD_NAME}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://komiku.org/"
}

def get_comic_id_and_display_name(url):
    path = urlparse(url).path
    comic_id = path.split("/")[-2] if path.endswith("/") else path.split("/")[-1]
    comic_id = comic_id.replace("manga-", "").replace("/", "")
    display_name = " ".join(word.capitalize() for word in comic_id.split("-"))
    logging.info(f"Nama komik dari URL: ID={comic_id}, Display={display_name}")
    return comic_id, display_name

def fetch_page(url, retries=3, delay=2):
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
                error_msg = f"Tidak bisa mengambil {url} setelah {retries} percobaan."
                logging.error(error_msg)
                error_summary.append(error_msg)
                return None
    return None

def paraphrase_synopsis(original_synopsis):
    if not original_synopsis or original_synopsis == "No synopsis available.":
        return "Petualangan epik di dunia fantasi yang penuh dengan sihir dan misteri."
    # Filter teks promosi
    promo_phrases = [
        "baca komik", "bahasa indonesia", "di komiku", "komiku", "baca manga",
        "baca manhua", "baca manhwa", "selengkapnya", "klik di sini"
    ]
    filtered_synopsis = original_synopsis.lower()
    for phrase in promo_phrases:
        filtered_synopsis = filtered_synopsis.replace(phrase, "").strip()
    if not filtered_synopsis:
        return "Petualangan epik di dunia fantasi yang penuh dengan sihir dan misteri."
    # Parafrase
    phrase_map = {
        "perjalanan": ["petualangan", "kisah", "cerita"],
        "sihir": ["magis", "kekuatan ajaib", "ilmu sihir"],
        "kekuasaan": ["ambisi", "dominasi", "kuasa"],
        "intrik politik": ["konspirasi politik", "persaingan politik", "intrik kekuasaan"],
        "fantasi": ["dunia imajiner", "alam fantasi", "dunia ajaib"],
        "menghadapi": ["melawan", "berhadapan dengan", "menantang"]
    }
    words = filtered_synopsis.split()
    paraphrased = []
    for word in words:
        new_word = phrase_map.get(word.lower(), word)
        if isinstance(new_word, list):
            new_word = new_word[0]
        paraphrased.append(new_word)
    new_synopsis = " ".join(paraphrased).capitalize()
    if "petualangan" in new_synopsis.lower():
        new_synopsis = f"Seorang penyihir legendaris memulai {new_synopsis} yang mendebarkan."
    elif "konspirasi" in new_synopsis.lower():
        new_synopsis = f"{new_synopsis} di tengah dunia yang penuh dengan rahasia dan bahaya."
    logging.info(f"Sinopsis asli: {original_synopsis}")
    logging.info(f"Sinopsis setelah parafrase: {new_synopsis}")
    return new_synopsis

def scrape_komiku_details(url, soup):
    # Title
    title_element = soup.find("h1")
    title = title_element.text.strip() if title_element else "Unknown Title"
    # Bersihkan "Komik" dari judul
    title = title.replace("Komik ", "").replace("komik ", "").strip()
    logging.info(f"Nama komik dari <h1>: {title}")

    # Author
    author = "Unknown Author"
    selectors = [
        (soup.find, "table", {"class": "inftable"}, lambda x: x.find("td", string=lambda t: "Pengarang" in t if t else False)),
        (soup.find, "span", {"string": lambda x: "Author" in x if x else False}, lambda x: x.find_next("span")),
        (soup.find, "td", {"string": lambda x: "Author" in x if x else False}, lambda x: x.find_next("td")),
        (soup.find, "div", {"class": "komik_info-content-meta"}, lambda x: x.find("span", string=lambda t: "Author" in t if t else False)),
        (soup.find_all, "span", {}, lambda x: x if "Author" in x.text else None)
    ]
    for find_method, tag, attrs, next_step in selectors:
        element = find_method(tag, **attrs) if attrs else find_method(tag)
        if element:
            if isinstance(element, list):
                for span in element:
                    next_text = span.find_next_sibling(text=True)
                    if next_text and next_text.strip():
                        author = next_text.strip()
                        break
            else:
                next_element = next_step(element)
                if next_element:
                    if tag == "table":
                        author = next_element.find_next("td").text.strip() if next_element.find_next("td") else "Unknown Author"
                    else:
                        author = next_element.text.strip()
                    if author and author != "Unknown Author":
                        break
                elif element.find_next_sibling(text=True):
                    author = element.find_next_sibling(text=True).strip()
                    if author and author != "Unknown Author":
                        break
    author = author.replace("~", "").strip() if author else "Unknown Author"
    logging.info(f"Author ditemukan: {author}")

    # Genre
    genre = "Fantasy"
    genre_selectors = [
        (soup.find, "table", {"class": "inftable"}, lambda x: x.find("td", string=lambda t: "Konsep Cerita" in t if t else False)),
        (soup.find, "span", {"string": lambda x: "Genre" in x if x else False}, lambda x: x.find_next("span")),
        (soup.find, "td", {"string": lambda x: "Genre" in x if x else False}, lambda x: x.find_next("td")),
        (soup.find, "div", {"class": "komik_info-content-genre"}, lambda x: x)
    ]
    for find_method, tag, attrs, next_step in genre_selectors:
        element = find_method(tag, **attrs)
        if element:
            next_element = next_step(element)
            if next_element:
                if tag == "table":
                    genre = next_element.find_next("td").text.strip() if next_element.find_next("td") else "Fantasy"
                else:
                    genre = next_element.text.strip()
                if genre:
                    break
    logging.info(f"Genre ditemukan: {genre}")

    # Type
    comic_type = "Manhua"
    type_selectors = [
        (soup.find, "table", {"class": "inftable"}, lambda x: x.find("td", string=lambda t: "Jenis Komik" in t if t else False)),
        (soup.find, "span", {"string": lambda x: "Type" in x if x else False}, lambda x: x.find_next("span")),
        (soup.find, "td", {"string": lambda x: "Type" in x if x else False}, lambda x: x.find_next("td")),
        (soup.find, "div", {"class": "komik_info-content-meta"}, lambda x: x.find("span", string=lambda t: "Type" in t if t else False))
    ]
    for find_method, tag, attrs, next_step in type_selectors:
        element = find_method(tag, **attrs)
        if element:
            next_element = next_step(element)
            if next_element:
                if tag == "table":
                    comic_type = next_element.find_next("td").text.strip() if next_element.find_next("td") else "Manhua"
                else:
                    comic_type = next_element.text.strip()
                if comic_type:
                    break
            elif element.find_next_sibling(text=True):
                comic_type = element.find_next_sibling(text=True).strip()
                if comic_type:
                    break
    logging.info(f"Tipe komik ditemukan: {comic_type}")

    # Synopsis
    synopsis = "No synopsis available."
    synopsis_element = soup.find("div", class_="desc")
    if synopsis_element:
        synopsis = synopsis_element.text.strip()
    else:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            synopsis = meta_desc["content"].strip()
    synopsis = paraphrase_synopsis(synopsis)

    # Cover
    cover_url = ""
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
    logging.info(f"Scraped data: title={title}, author={author}, genre={genre}, type={comic_type}, synopsis={synopsis}, cover={cover_url}")
    return title, author, synopsis, cover_url, soup, genre, comic_type

def scrape_comic_details(url):
    html = fetch_page(url)
    if not html:
        return None, None, None, None, None, None, None
    soup = BeautifulSoup(html, "html.parser")
    domain = urlparse(url).netloc
    if "komiku.org" in domain:
        return scrape_komiku_details(url, soup)
    else:
        logging.warning(f"Situs tidak dikenal: {domain}. Menggunakan default Komiku.")
        return scrape_komiku_details(url, soup)
    return None, None, None, None, None, None, None

def scrape_chapter_list(url, soup):
    chapters = {}
    logging.info(f"Mencari daftar chapter dari {url}...")
    chapter_elements = soup.select("td.judulseries a")
    if not chapter_elements:
        logging.warning("Tidak ditemukan chapter. Mencoba fallback...")
        all_links = soup.select("a[href*='chapter']")
        for link in all_links:
            href = link.get("href", "")
            if "chapter" in href.lower():
                # Ekstrak nomor chapter dengan regex, tangani desimal
                chapter_text = link.text.strip()
                match = re.search(r'Chapter\s+(\d+(\.\d+)?)', chapter_text, re.IGNORECASE)
                if match:
                    chapter_num = match.group(1)  # Ambil nomor termasuk desimal (36, 36.5, dll.)
                    chapters[chapter_num] = href
                    logging.info(f"Chapter {chapter_num} ditemukan via fallback: {href}")
                else:
                    logging.warning(f"Format chapter tidak dikenali: {chapter_text}")
    for element in chapter_elements:
        href = element.get("href", "")
        chapter_text = element.text.strip()
        # Ekstrak nomor chapter dengan regex, tangani desimal
        match = re.search(r'Chapter\s+(\d+(\.\d+)?)', chapter_text, re.IGNORECASE)
        if match:
            chapter_num = match.group(1)  # Ambil nomor termasuk desimal
            chapters[chapter_num] = href
            logging.info(f"Chapter {chapter_num}: {href}")
        else:
            logging.warning(f"Format chapter tidak dikenali: {chapter_text}")
    return chapters

def scrape_chapter_images(chapter_url):
    full_url = urljoin("https://komiku.org", chapter_url)
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
        if image_elements:
            for img in image_elements:
                src = img.get("src", "")
                if src and src.startswith("http"):
                    image_urls.append(src)
            break
    if not image_urls:
        error_msg = f"Tidak ada gambar untuk chapter ini: {chapter_url}"
        logging.error(error_msg)
        error_summary.append(error_msg)
    return image_urls

def upload_to_cloudinary(image_url, comic_id, chapter_num):
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
        error_msg = f"Gagal upload gambar {image_url} ke Cloudinary: {e}"
        logging.error(error_msg)
        error_summary.append(error_msg)
        return image_url

def add_comic(url):
    start_time = time.time()
    logging.info(f"Menambahkan komik baru: {url}")
    comic_id, _ = get_comic_id_and_display_name(url)
    title, author, synopsis, cover_url, soup, genre, comic_type = scrape_comic_details(url)
    if not title:
        error_msg = "Gagal mendapatkan detail komik. Proses dihentikan."
        logging.error(error_msg)
        error_summary.append(error_msg)
        return
    comic_data = {
        "title": title if title else "Unknown Title",
        "author": author if author else "Unknown Author",
        "synopsis": synopsis if synopsis else "No synopsis available.",
        "cover": cover_url if cover_url else "",
        "genre": genre if genre else "Fantasy",
        "type": comic_type if comic_type else "Manhua",
        "chapters": {}
    }
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if os.path.exists(comic_file):
        with open(comic_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            comic_data["chapters"] = existing_data.get("chapters", {})
        logging.info(f"Komik sudah ada, mempertahankan chapters dari {comic_file}")
    logging.info(f"Comic Data sebelum disimpan: {json.dumps(comic_data, indent=2)}")
    with open(comic_file, "w", encoding="utf-8") as f:
        json.dump(comic_data, f, indent=4)
    logging.info(f"Berhasil simpan data komik ke {comic_file}")
    update_index(comic_id, comic_data)
    end_time = time.time()
    logging.info(f"Penambahan komik selesai dalam {end_time - start_time:.2f} detik.")

def update_comic(url, start_chapter, end_chapter, overwrite=False):
    start_time = time.time()
    logging.info(f"Mulai update chapter: {url}")
    comic_id, _ = get_comic_id_and_display_name(url)
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if not os.path.exists(comic_file):
        error_msg = f"File {comic_file} tidak ada. Jalankan 'add-comic' dulu."
        logging.error(error_msg)
        error_summary.append(error_msg)
        return
    with open(comic_file, "r", encoding="utf-8") as f:
        comic_data = json.load(f)
    html = fetch_page(url)
    if not html:
        error_msg = "Gagal mengambil halaman komik."
        logging.error(error_msg)
        error_summary.append(error_msg)
        return
    soup = BeautifulSoup(html, "html.parser")
    chapters = scrape_chapter_list(url, soup)
    if not chapters:
        error_msg = "Tidak ada chapter yang ditemukan."
        logging.error(error_msg)
        error_summary.append(error_msg)
        return
    first_image_url = None
    for chapter_num in chapters.keys():
        chapter_num_float = float(chapter_num)  # Ubah ke float untuk perbandingan
        if start_chapter <= chapter_num_float <= end_chapter:
            if str(chapter_num) in comic_data["chapters"] and not overwrite:
                logging.info(f"Chapter {chapter_num} sudah ada, melewati.")
                continue
            if str(chapter_num) in comic_data["chapters"] and overwrite:
                logging.info(f"Overwrite diaktifkan: Menghapus data lama chapter {chapter_num} dan download ulang.")
                del comic_data["chapters"][str(chapter_num)]
            image_urls = scrape_chapter_images(chapters[chapter_num])
            if not image_urls:
                logging.warning(f"Chapter {chapter_num} dilewati karena tidak ada gambar.")
                continue
            uploaded_urls = []
            for idx, img_url in enumerate(image_urls, 1):
                uploaded_url = upload_to_cloudinary(img_url, comic_id, chapter_num)
                uploaded_urls.append(uploaded_url)
                if not first_image_url:
                    first_image_url = uploaded_url
            comic_data["chapters"][str(chapter_num)] = {"pages": uploaded_urls}
    if first_image_url and (not comic_data["cover"] or fetch_page(comic_data["cover"]) is None):
        logging.info(f"Cover asli gagal, ganti dengan: {first_image_url}")
        comic_data["cover"] = first_image_url
    logging.info(f"Comic Data sebelum disimpan: {json.dumps(comic_data, indent=2)}")
    with open(comic_file, "w", encoding="utf-8") as f:
        json.dump(comic_data, f, indent=4)
    logging.info(f"Berhasil disimpan ke {comic_file}")
    update_index(comic_id, comic_data)
    end_time = time.time()
    logging.info(f"Update selesai dalam {end_time - start_time:.2f} detik.")

def update_index(comic_id, comic_data):
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = {}
    if os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            if not isinstance(index_data, dict):
                logging.warning(f"Invalid index.json format: {index_data}. Resetting.")
                index_data = {}
        except Exception as e:
            error_msg = f"Gagal membaca index.json: {e}. Resetting."
            logging.error(error_msg)
            error_summary.append(error_msg)
            index_data = {}
    comic_entry = {
        "title": comic_data["title"],
        "synopsis": comic_data["synopsis"],
        "cover": comic_data["cover"],
        "genre": comic_data["genre"],
        "type": comic_data["type"],
        "total_chapters": len(comic_data["chapters"])
    }
    index_data[comic_id] = comic_entry
    logging.info(f"Index Data sebelum disimpan: {json.dumps(index_data, indent=2)}")
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=4)
    logging.info(f"Berhasil update indeks di {index_file}")

def push_to_github():
    logging.info("Push perubahan ke GitHub...")
    try:
        data_path = os.path.abspath(DATA_DIR)
        subprocess.run(["git", "add", data_path], check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            logging.info("Tidak ada perubahan. Skip push.")
            return True
        commit = subprocess.run(
            ["git", "commit", "-m", "Update comic data and layout"],
            capture_output=True, text=True
        )
        if commit.returncode != 0:
            error_msg = f"Commit gagal: {commit.stderr}"
            logging.error(error_msg)
            error_summary.append(error_msg)
            return False
        push = subprocess.run(
            ["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", "main"],
            capture_output=True, text=True
        )
        if push.returncode != 0:
            error_msg = f"Push gagal: {push.stderr}"
            logging.error(error_msg)
            error_summary.append(error_msg)
            return False
        logging.info("Berhasil push ke GitHub.")
        return True
    except Exception as e:
        error_msg = f"Error push: {e}"
        logging.error(error_msg)
        error_summary.append(error_msg)
        return False

def main():
    logging.info("=== Mulai Proses Update Komik ===")
    parser = argparse.ArgumentParser(description="GreedyComicHub Scraper")
    subparsers = parser.add_subparsers(dest="command")
    parser_add = subparsers.add_parser("add-comic", help="Add new comic details")
    parser_add.add_argument("url", help="Comic URL")
    parser_update = subparsers.add_parser("update", help="Update comic chapters")
    parser_update.add_argument("url", help="Comic URL")
    parser_update.add_argument("--start", type=int, default=1, help="Start chapter")
    parser_update.add_argument("--end", type=int, default=1, help="End chapter")
    parser_update.add_argument("--overwrite", action="store_true", help="Overwrite existing chapters")
    args = parser.parse_args()
    try:
        if args.command == "add-comic":
            add_comic(args.url)
            push_to_github()
            logging.info(f"Added comic {args.url}")
        elif args.command == "update":
            update_comic(args.url, args.start, args.end, overwrite=args.overwrite)
            push_to_github()
            logging.info(f"Updated chapters for {args.url}")
        else:
            parser.print_help()
    except Exception as e:
        error_msg = f"Proses update gagal: {str(e)}"
        logging.error(error_msg)
        error_summary.append(error_msg)
    finally:
        logging.info("=== Proses Update Selesai ===")
        # Rekap error di akhir (hanya level ERROR)
        if error_summary:
            logging.info("=== Rekap Error ===")
            for error in error_summary:
                logging.error(error)
            logging.info(f"Total Error: {len(error_summary)}")
        else:
            logging.info("Tidak ada error selama proses update. Semua aman!")

if __name__ == "__main__":
    main()