# update_chapters.py: Update semua chapter untuk semua komik di index.json
import logging
import os
import subprocess
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import read_json, write_json, fetch_page, DATA_DIR, push_to_github
from scraper import scrape_chapter_list, scrape_chapter_images
from update_comic import get_comic_id_from_url
from datetime import datetime

def update_all_chapters(start=None, overwrite=False):
    """Update hanya chapter baru untuk semua komik berdasarkan index.json."""
    logging.info("Mengecek dan mengupdate chapter baru untuk semua komik...")
    index_file = os.path.join(DATA_DIR, "index.json")
    updates_file = os.path.join(DATA_DIR, "updates.json")
    index_data = read_json(index_file) or {}
    updates_data = read_json(updates_file) or {}
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

        # Baca chapter lokal
        comic_data = read_json(comic_file)
        chapters = comic_data.get("chapters", {})
        comic_title = comic_info.get("title", comic_id)
        existing_chapters = set(float(ch) for ch in chapters.keys()) if chapters else set()

        # Ambil daftar chapter dari web
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

        # Konversi web_chapters ke set numerik buat perbandingan
        web_chapter_nums = {float(ch): url for ch, url in web_chapters.items()}
        new_chapters = {ch for ch in web_chapter_nums.keys() if ch not in existing_chapters and (start is None or ch >= float(start))}

        if not new_chapters:
            logging.info(f"Komik {comic_title}: Ga ada chapter baru ditemuin.")
            continue

        logging.info(f"Komik {comic_title}: Temuin {len(new_chapters)} chapter baru, mulai dari {min(new_chapters)}")

        # Update hanya chapter baru
        for chapter_num in sorted(new_chapters):
            chapter_num_str = str(chapter_num)
            chapter_url = web_chapters.get(chapter_num_str)
            if not chapter_url:
                for key, url in web_chapters.items():
                    if float(key) == chapter_num:
                        chapter_url = url
                        break
            if not chapter_url:
                logging.warning(f"Chapter {chapter_num} ga ditemuin di web_chapters, lewati.")
                continue

            # Scrape gambar
            images = scrape_chapter_images(chapter_url)
            logging.info(f"Scraped {len(images)} images for Chapter {chapter_num}")

            chapters[chapter_num_str] = {
                "title": f"Chapter {chapter_num}",
                "url": chapter_url,
                "images": images
            }
            # Catat di updates.json
            updates_data[f"{comic_id}_{chapter_num}"] = {
                "comic_id": comic_id,
                "title": comic_title,
                "chapter": chapter_num,
                "thumbnail": comic_info.get("cover", "placeholder.jpg"),
                "timestamp": datetime.utcnow().isoformat()
            }
            logging.info(f"Komik {comic_title}: Berhasil update chapter {chapter_num}")

        # Simpan ke file
        comic_data["chapters"] = chapters
        comic_data["total_chapters"] = len(chapters)
        write_json(comic_file, comic_data)
        write_json(updates_file, updates_data)

        # Update index.json
        index_data[comic_id]["total_chapters"] = len(chapters)
        write_json(index_file, index_data)

    # Rekap
    logging.info("Selesai update-chapters!")
    if failed_comics:
        logging.info("\n=== Komik yang tidak di-update ===")
        for comic_id in set(failed_comics):
            comic_url = index_data.get(comic_id, {}).get("source_url", f"https://komiku.org/manga/{comic_id}")
            logging.info(f"- {comic_id}: {comic_url}")
    else:
        logging.info("Semua komik berhasil diupdated, bro!")

    # Auto deploy ke web
    logging.info("Mulai auto deploy ke web...")
    try:
        files_to_deploy = ["index.html", "style.css", "data/index.json", "data/updates.json"]
        subprocess.run(["git", "add"] + files_to_deploy, check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            logging.info("Tidak ada perubahan. Skip deploy.")
            return
        subprocess.run(["git", "commit", "-m", "Auto deploy after update-chapters"], check=True)
        push_to_github()
        logging.info("Auto deploy selesai!")
    except subprocess.CalledProcessError as e:
        logging.error(f"Gagal auto deploy: {e}")
    except Exception as e:
        logging.error(f"Error lain saat auto deploy: {e}")

if __name__ == "__main__":
    from utils import setup_logging
    setup_logging()
    update_all_chapters()