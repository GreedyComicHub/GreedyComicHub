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

    successful_comics = []
    failed_comics = []

    for comic_id in index_data:
        comic_url = index_data[comic_id].get("source_url")
        if not comic_url:
            logging.error(f"Komik {comic_id} nggak punya source_url di index.json. Lewati.")
            failed_comics.append((comic_id, f"https://komiku.org/manga/{comic_id}"))
            continue
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} nggak ada. Lewati.")
            failed_comics.append((comic_id, comic_url))
            continue

        comic_data = read_json(comic_file)
        chapters = comic_data.get("chapters", {})
        if not chapters:
            logging.info(f"Komik {comic_id}: Belum ada chapter, coba add chapter pertama.")
            try:
                update_comic(comic_url, 1.0, 1.0, overwrite=False)
                successful_comics.append(comic_id)
            except Exception as e:
                logging.error(f"Komik {comic_id}: Gagal add chapter pertama: {e}")
                failed_comics.append((comic_id, comic_url))
            continue

        latest_local_chapter = max([float(ch) for ch in chapters.keys()])
        comic_title = index_data[comic_id].get("title", comic_id)
        logging.info(f"Komik {comic_id}: Chapter terakhir di JSON = {latest_local_chapter}")

        html = fetch_page(comic_url)
        if not html:
            logging.error(f"Gagal mengambil halaman {comic_url}. Lewati.")
            failed_comics.append((comic_id, comic_url))
            continue
        soup = BeautifulSoup(html, "html.parser")
        chapters = scrape_chapter_list(comic_url, soup)
        if not chapters:
            logging.warning(f"Nggak ada chapter ditemukan untuk {comic_id}. Lewati.")
            failed_comics.append((comic_id, comic_url))
            continue

        web_chapters = sorted([float(ch) for ch in chapters.keys()])
        new_chapters = [ch for ch in web_chapters if ch > latest_local_chapter]
        if not new_chapters:
            logging.info(f"Komik {comic_title}: Belum ada chapter baru setelah {latest_local_chapter}, bro!")
            successful_comics.append(comic_id)
            continue

        next_chapter = min(new_chapters)
        logging.info(f"Komik {comic_id}: Coba update chapter {next_chapter}")
        try:
            update_comic(comic_url, next_chapter, next_chapter, overwrite=False)
            successful_comics.append(comic_id)
        except Exception as e:
            logging.error(f"Komik {comic_id}: Gagal update chapter {next_chapter}: {e}")
            failed_comics.append((comic_id, comic_url))

    logging.info("===========selesai==========")
    logging.info(f"{len(successful_comics)} komik berhasil diupdate bro!")
    if failed_comics:
        logging.info(f"{len(failed_comics)} komik gagal update:")
        for comic_id, comic_url in failed_comics:
            logging.info(f"- {comic_url}")
    else:
        logging.info("0 komik gagal update.")