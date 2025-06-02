import logging
import os
from scraper import scrape_chapter_list
from update_comic import update_comic
from utils import read_json, fetch_page, DATA_DIR
from bs4 import BeautifulSoup

def update_all():
    """Update chapter berikutnya berdasarkan chapter terakhir di website GreedyComicHub."""
    logging.info("Mengecek chapter berikutnya untuk semua komik...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    
    if not index_data:
        logging.warning("Nggak ada komik di index.json, bro!")
        return

    for comic_id in index_data:
        comic_url = f"https://komiku.org/manga/{comic_id}"
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} nggak ada. Lewati.")
            continue
        
        # Baca total_chapters dari index.json (acuan website)
        latest_local_chapter = float(index_data[comic_id].get("total_chapters", 0))
        comic_title = index_data[comic_id].get("title", comic_id)
        logging.info(f"Komik {comic_id}: Chapter terakhir di website = {latest_local_chapter}")

        # Chapter yang mau diupdate (next chapter)
        next_chapter = latest_local_chapter + 1
        logging.info(f"Komik {comic_id}: Coba update chapter {next_chapter}")

        # Scrape daftar chapter dari komiku.org
        html = fetch_page(comic_url)
        if not html:
            logging.error(f"Gagal mengambil halaman {comic_url}. Lewati.")
            continue
        soup = BeautifulSoup(html, "html.parser")
        chapters = scrape_chapter_list(comic_url, soup)
        if not chapters:
            logging.warning(f"Nggak ada chapter ditemukan untuk {comic_id}. Lewati.")
            continue
        
        # Cek apakah next_chapter ada di web
        web_chapters = sorted([float(ch) for ch in chapters.keys()])
        if next_chapter not in web_chapters:
            logging.info(f"Komik {comic_title}: Belum ada chapter {next_chapter}, bro!")
            continue

        # Update hanya next_chapter
        logging.info(f"Komik {comic_id}: Nambah chapter {next_chapter}")
        update_comic(comic_url, next_chapter, next_chapter, overwrite=False)
    logging.info("Selesai cek update-all!")