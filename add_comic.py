import logging
import os
from scraper import scrape_komiku_details, scrape_chapter_list, get_comic_id_and_display_name
from update_comic import update_comic
from utils import read_json, write_json, fetch_page, DATA_DIR
from bs4 import BeautifulSoup

def add_comic(url):
    """Tambah komik baru dari URL komiku.org."""
    logging.info(f"Menambahkan komik baru: {url}")
    comic_id, display_name = get_comic_id_and_display_name(url)
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file) or {}

    if comic_id in index_data:
        logging.warning(f"Komik {comic_id} udah ada di index.json, bro! Skip.")
        return

    html = fetch_page(url)
    if not html:
        logging.error(f"Gagal mengambil halaman {url}.")
        return
    soup = BeautifulSoup(html, "html.parser")
    details = scrape_komiku_details(url, soup)
    if not details:
        logging.error(f"Gagal scrape detail komik {url}.")
        return

    index_data[comic_id] = {
        "source_url": url,
        "title": details["title"],
        "synopsis": details["synopsis"],
        "cover": details["cover"],
        "genre": details["genre"],
        "type": details["type"],
        "total_chapters": 0
    }
    write_json(index_file, index_data)
    logging.info(f"Berhasil nambah {comic_id} ke index.json")

    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    write_json(comic_file, {"chapters": {}})
    logging.info(f"Berhasil buat file {comic_file}")

    update_comic(url, 1.0, 1.0, overwrite=False)
    logging.info(f"Berhasil update chapter pertama untuk {comic_id}")