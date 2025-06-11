import logging
import os
from scraper import scrape_chapter_list
from update_comic import update_comic
from utils import read_json, fetch_page, DATA_DIR
from bs4 import BeautifulSoup

def update_all(start=None, end=None, overwrite=False):
    """Update chapter berikutnya untuk semua komik berdasarkan index.json."""
    logging.info("Mengecek chapter berikutnya untuk semua komik...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file) or {}
    if not index_data:
        logging.warning("Ga ada komik di index.json, bro!")
        return

    failed_comics = []
    for comic_id, comic_info in index_data.items():
        comic_url = comic_info.get("source_url", f"https://komiku.org/manga/{comic_id}")
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} ga ada. Lewati.")
            failed_comics.append(comic_id)
            continue

        # Baca chapter terakhir
        comic_data = read_json(comic_file)
        chapters = comic_data.get("chapters", {})
        comic_title = comic_info.get("title", comic_id)

        if not chapters:
            logging.info(f"Komik {comic_title}: Belum ada chapter, coba add chapter pertama.")
            try:
                update_comic(comic_url, start or 1, start or 1, overwrite)
            except Exception as e:
                logging.error(f"Komik {comic_title}: Gagal add chapter pertama: {e}")
                failed_comics.append(comic_id)
            continue

        # Ambil chapter terakhir
        latest_local_chapter = max([float(ch) for ch in chapters.keys()])
        latest_local_chapter = int(latest_local_chapter) if latest_local_chapter.is_integer() else latest_local_chapter
        logging.info(f"Komik {comic_title}: Chapter terakhir di JSON = {latest_local_chapter}")

        # Scrape daftar chapter dari web
        html = fetch_page(comic_url)
        if not html:
            logging.error(f"Gagal ambil halaman {comic_url}. Lewati.")
            failed_comics.append(comic_id)
            continue

        soup = BeautifulSoup(html, "html.parser")
        web_chapters = scrape_chapter_list(comic_url, soup)
        if not web_chapters:
            logging.warning(f"Ga ada chapter ditemukan untuk {comic_title}. Lewati.")
            failed_comics.append(comic_id)
            continue

        # Filter chapter berikutnya
        new_chapters = [ch for ch in web_chapters.keys() if float(ch) > latest_local_chapter]
        if not new_chapters:
            logging.info(f"Komik {comic_title}: Belum ada chapter baru setelah {latest_local_chapter}")
            failed_comics.append(comic_id)
            continue

        # Ambil chapter berikutnya
        next_chapter = min([float(ch) for ch in new_chapters])
        next_chapter = int(next_chapter) if next_chapter.is_integer() else next_chapter
        logging.info(f"Komik {comic_title}: Coba update chapter {next_chapter}")

        try:
            update_comic(comic_url, next_chapter, next_chapter, overwrite)
            logging.info(f"Komik {comic_title}: Berhasil update chapter {next_chapter}")
        except Exception as e:
            logging.error(f"Komik {comic_title}: Gagal update chapter {next_chapter}: {e}")
            failed_comics.append(comic_id)

    # Rekap
    logging.info("Selesai update-all!")
    if failed_comics:
        logging.info("\n=== Komik yang tidak di-update ===")
        for comic_id in set(failed_comics):
            comic_url = index_data.get(comic_id, {}).get("source_url", f"https://komiku.org/manga/{comic_id}")
            logging.info(f"- {comic_id}: {comic_url}")
    else:
        logging.info("Semua komik berhasil diupdate, bro!")