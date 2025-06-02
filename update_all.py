import logging
import os
from scraper import scrape_chapter_list, get_comic_id_and_display_name
from update_comic import update_comic
from utils import read_json, fetch_page, DATA_DIR
from bs4 import BeautifulSoup

def update_all():
    """Update semua komik dengan menambah chapter baru secara otomatis."""
    logging.info("Memperbarui semua komik secara otomatis...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    
    if not index_data:
        logging.warning("Tidak ada komik di index.json.")
        return

    for comic_id in index_data:
        comic_url = f"https://komiku.org/manga/{comic_id}"
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} tidak ada. Lewati.")
            continue
        
        # Baca data komik lokal
        comic_data = read_json(comic_file)
        local_chapters = sorted([float(ch) for ch in comic_data.get("chapters", {}).keys()])
        latest_local_chapter = local_chapters[-1] if local_chapters else 0.0
        logging.info(f"Komik {comic_id}: Chapter terakhir lokal = {latest_local_chapter}")

        # Scrape daftar chapter dari website
        html = fetch_page(comic_url)
        if not html:
            logging.error(f"Gagal mengambil halaman {comic_url}. Lewati.")
            continue
        soup = BeautifulSoup(html, "html.parser")
        chapters = scrape_chapter_list(comic_url, soup)
        if not chapters:
            logging.warning(f"Tidak ada chapter ditemukan untuk {comic_id}. Lewati.")
            continue
        
        # Cari chapter baru
        web_chapters = sorted([float(ch) for ch in chapters.keys()])
        latest_web_chapter = web_chapters[-1] if web_chapters else 0.0
        new_chapters = [ch for ch in web_chapters if ch > latest_local_chapter]

        if not new_chapters:
            logging.info(f"Komik {comic_data['title']} belum ada update terbaru.")
            continue

        # Update chapter baru
        logging.info(f"Komik {comic_id}: Ditemukan {len(new_chapters)} chapter baru: {new_chapters}")
        start_chapter = min(new_chapters)
        end_chapter = max(new_chapters)
        update_comic(comic_url, start_chapter, end_chapter, overwrite=False)
    logging.info("Selesai memperbarui semua komik.")