import logging
import os
from scraper import scrape_chapter_list
from update_comic import update_comic
from utils import read_json, fetch_page, DATA_DIR
from bs4 import BeautifulSoup

def update_all():
    logging.info("Mengecek chapter baru...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    failed_comics = []
    
    if not index_data:
        logging.warning("Nggak ada komik di index.json!")
        return

    for comic_id, comic_info in index_data.items():
        comic_url = comic_info.get("source_url", f"https://komiku.org/manga/{comic_id}")
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} nggak ada.")
            failed_comics.append(f"{comic_id} ({comic_url})")
            continue
        
        comic_data = read_json(comic_file)
        local_chapters = sorted([float(ch) for ch in comic_data.get("chapters", {}).keys()])
        latest_local_chapter = local_chapters[-1] if local_chapters else 0.0
        logging.info(f"{comic_id}: Chapter ter: {latest_local_chapter}")

        next_chapter = latest_local_chapter + 1
        if str(next_chapter) in comic_data.get("chapters", {}):
            continue

        html = fetch_page(comic_url)
        if not html:
            logging.error(f"Gagal ambil {comic_url}. {comic_id} gagal.")
            failed_comics.append(f"{comic_id} ({comic_url})")
            continue
        soup = BeautifulSoup(html, "html.parser")
        chapters = scrape_chapter_list(comic_url, soup)
        if not chapters:
            logging.warning(f"No chapter untuk {comic_id}.")
            failed_comics.append(f"{comic_id} ({comic_url})")
            continue
        
        web_chapters = sorted([float(ch) for ch in chapters.keys()])
        if next_chapter not in web_chapters:
            logging.info(f"{comic_id}: No chapter {next_chapter}.")
            continue

        try:
            logging.info(f"Update {comic_id} chapter {next_chapter}")
            update_comic(comic_url, next_chapter, next_chapter, overwrite=False)
        except Exception as e:
            logging.error(f"Gagal update {comic_id} chapter {next_chapter}: {e}")
            failed_comics.append(f"{comic_id} ({comic_url})")

    if failed_comics:
        logging.error(f"Gagal: {', '.join(failed_comics)}. Cek URL.")
    logging.info("Done.")