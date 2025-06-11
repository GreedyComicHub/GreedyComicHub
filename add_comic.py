import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import fetch_page, write_json, read_json, DATA_DIR, get_comic_id_from_url, upload_to_cloudinary
from scraper import scrape_komiku_details

def add_comic(url):
    logging.info(f"Mulai tambah komik: {url}")
    comic_id = get_comic_id_from_url(url)
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    index_file = os.path.join(DATA_DIR, "index.json")

    # Scrape metadata komik
    html = fetch_page(url)
    if not html:
        logging.error(f"Gagal ambil halaman {url}")
        return

    try:
        soup = BeautifulSoup(html, 'html.parser')
        title, author, synopsis, cover_url, _, genre, comic_type = scrape_komiku_details(url, soup)

        # Upload cover ke Cloudinary
        cover_cloudinary_url = upload_to_cloudinary(cover_url, comic_id, "cover") if cover_url and cover_url.startswith('http') else ""

        # Ambil data lama dari comic.json kalo ada
        existing_comic_data = read_json(comic_file) or {}
        chapters = existing_comic_data.get("chapters", {})
        total_chapters = len(chapters)

        # Buat comic data
        comic_data = {
            "title": title,
            "author": author,
            "genre": genre,
            "synopsis": synopsis,
            "cover": cover_cloudinary_url,
            "source_url": url,
            "chapters": chapters,
            "total_chapters": total_chapters
        }

        # Simpan ke <comic>.json (overwrite)
        write_json(comic_file, comic_data)
        logging.info(f"Berhasil disimpan (overwrite) ke {comic_file}")

        # Update index.json, jaga data lama
        index_data = read_json(index_file) or {}
        index_data[comic_id] = {
            "title": title,
            "author": author,
            "synopsis": synopsis,
            "cover": cover_cloudinary_url,
            "genre": genre,
            "type": comic_type,
            "total_chapters": total_chapters,
            "source_url": url
        }
        write_json(index_file, index_data)
        logging.info(f"Update {comic_id} di {index_file}")

    except Exception as e:
        logging.error(f"Error tambah komik {url}: {e}")