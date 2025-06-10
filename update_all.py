import logging
import os
<<<<<<< HEAD
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
    # List buat nyimpen komik yang gagal
    failed_comics = []
    for comic_id in index_data:
        comic_url = index_data[comic_id].get("source_url", f"https://komiku.org/manga/{comic_id}")
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} nggak ada. Lewati.")
            failed_comics.append(comic_id)
            continue
        # Baca chapter terakhir dari comic_id.json
        comic_data = read_json(comic_file)
        chapters = comic_data.get("chapters", {})
        if not chapters:
            logging.info(f"Komik {comic_id}: Belum ada chapter, coba add chapter pertama.")
            try:
                update_comic(comic_url, 1.0, 1.0, overwrite=False)
            except Exception as e:
                logging.error(f"Komik {comic_id}: Gagal add chapter pertama: {e}")
                failed_comics.append(comic_id)
            continue
        # Ambil chapter terakhir dengan sorting berdasarkan float
        latest_local_chapter = max([float(ch) for ch in chapters.keys()])
        comic_title = index_data[comic_id].get("title", comic_id)
        logging.info(f"Komik {comic_id}: Chapter terakhir di JSON = {latest_local_chapter}")
        # Scrape daftar chapter dari komiku.org
        html = fetch_page(comic_url)
        if not html:
            logging.error(f"Gagal mengambil halaman {comic_url}. Lewati.")
            failed_comics.append(comic_id)
            continue
        soup = BeautifulSoup(html, "html.parser")
        chapters = scrape_chapter_list(comic_url, soup)
        if not chapters:
            logging.warning(f"Nggak ada chapter ditemukan untuk {comic_id}. Lewati.")
            failed_comics.append(comic_id)
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
        try:
            logging.info(f"Komik {comic_id}: Nambah chapter {next_chapter}")
            update_comic(comic_url, next_chapter, next_chapter, overwrite=False)
        except Exception as e:
            logging.error(f"Komik {comic_id}: Gagal update chapter {next_chapter}: {e}")
            failed_comics.append(comic_id)
    # Rekap komik yang gagal di akhir
    logging.info("Selesai cek update-all!")
    if failed_comics:
        logging.error(f"Rekap komik yang gagal: {', '.join(set(failed_comics))}")
    else:
        logging.info("Semua komik berhasil diupdate, bro!")
=======
from urllib.parse import urlparse
from utils import read_json, write_json, DATA_DIR
from update_comic import update_comic

def update_all():
    """Update semua komik di index.json."""
    logging.info("Memulai update semua komik...")
    
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    
    if not index_data:
        logging.warning("index.json kosong")
        return
    
    for comic_id, comic_info in index_data.items():
        source_url = comic_info.get("source_url")
        if not source_url:
            logging.warning(f"Komik {comic_id} tidak punya source_url, lewati.")
            continue
        
        logging.info(f"Update komik: {comic_id}")
        update_comic(source_url, start_chapter=1.0, end_chapter=9999.0, overwrite=False)
    
    logging.info("Selesai update semua komik.")
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
