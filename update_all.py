import logging
import os
from scraper import scrape_chapter_list
from update_comic import update_comic
from utils import read_json, fetch_page, DATA_DIR
from bs4 import BeautifulSoup

def update_all():
    """Update chapter berikutnya (satu chapter, termasuk desimal) untuk semua komik berdasarkan data terakhir di comic JSON."""
    logging.info("Mengecek chapter berikutnya untuk semua komik...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)

    if not index_data:
        logging.warning("Nggak ada komik di index.json, bro!")
        return

    for comic_id in index_data:
        # Fix: Pake source_url dari index.json
        comic_url = index_data[comic_id].get("source_url", f"https://komiku.org/manga/{comic_id}")
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} nggak ada. Lewati.")
            continue

        # Baca chapter terakhir dari comic_id.json
        comic_data = read_json(comic_file)
        chapters = comic_data.get("chapters", {})
        if not chapters:
            logging.info(f"Komik {comic_id}: Belum ada chapter, coba add chapter pertama.")
            update_comic(comic_url, 1.0, 1.0, overwrite=False)
            continue

        # Ambil chapter terakhir dengan sorting berdasarkan float
        latest_local_chapter = max([float(ch) for ch in chapters.keys()])
        comic_title = index_data[comic_id].get("title", comic_id)
        logging.info(f"Komik {comic_id}: Chapter terakhir di JSON = {latest_local_chapter}")

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

        # Filter chapter berikutnya (paling kecil di atas latest_local_chapter, termasuk desimal)
        web_chapters = sorted([float(ch) for ch in chapters.keys()])
        new_chapters = [ch for ch in web_chapters if ch > latest_local_chapter]
        if not new_chapters:
            logging.info(f"Komik {comic_title}: Belum ada chapter baru setelah {latest_local_chapter}, bro!")
            continue

        # Ambil chapter berikutnya (paling kecil dari new_chapters)
        next_chapter = min(new_chapters)
        logging.info(f"Komik {comic_id}: Coba update chapter {next_chapter}")

        # Update hanya next_chapter
        logging.info(f"Komik {comic_id}: Nambah chapter {next_chapter}")
        update_comic(comic_url, next_chapter, next_chapter, overwrite=False)
    logging.info("Selesai cek update-all!")