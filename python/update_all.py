# update_all.py: Update semua komik di index.json dan catat update di updates.json
import logging
import os
import subprocess
from scraper import scrape_chapter_list
from update_comic import update_comic
from utils import read_json, write_json, fetch_page, DATA_DIR, push_to_github
from bs4 import BeautifulSoup
from datetime import datetime

def update_all(start=None, end=None, overwrite=False):
    """Update chapter berikutnya untuk semua komik berdasarkan index.json."""
    logging.info("Mengecek chapter berikutnya untuk semua komik...")
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

        # Baca chapter terakhir
        comic_data = read_json(comic_file)
        chapters = comic_data.get("chapters", {})
        comic_title = comic_info.get("title", comic_id)

        if not chapters:
            logging.info(f"Komik {comic_title}: Belum ada chapter, coba add chapter pertama.")
            try:
                update_comic(comic_url, start or 1, start or 1, overwrite)
                # Catat di updates.json
                updates_data[f"{comic_id}_1"] = {
                    "comic_id": comic_id,
                    "title": comic_title,
                    "chapter": 1.0,
                    "thumbnail": comic_info.get("cover", "placeholder.jpg"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                write_json(updates_file, updates_data)
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
            continue

        # Ambil chapter berikutnya
        next_chapter = min([float(ch) for ch in new_chapters])
        next_chapter = int(next_chapter) if next_chapter.is_integer() else next_chapter
        logging.info(f"Komik {comic_title}: Coba update chapter {next_chapter}")

        try:
            update_comic(comic_url, next_chapter, next_chapter, overwrite)
            logging.info(f"Komik {comic_title}: Berhasil update chapter {next_chapter}")
            # Catat di updates.json
            updates_data[f"{comic_id}_{next_chapter}"] = {
                "comic_id": comic_id,
                "title": comic_title,
                "chapter": next_chapter,
                "thumbnail": comic_info.get("cover", "placeholder.jpg"),
                "timestamp": datetime.utcnow().isoformat()
            }
            write_json(updates_file, updates_data)
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
        logging.info("Semua komik berhasil diupdated, bro!")

    # Auto deploy ke web
    logging.info("Mulai auto deploy ke web...")
    try:
        # Tambah file spesifik
        files_to_deploy = ["index.html", "style.css", "data/index.json", "data/updates.json"]
        subprocess.run(["git", "add"] + files_to_deploy, check=True)
        # Cek perubahan
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            logging.info("Tidak ada perubahan. Skip deploy.")
            return
        # Commit
        subprocess.run(["git", "commit", "-m", "Auto deploy after update-all"], check=True)
        # Push
        push_to_github()
        logging.info("Auto deploy selesai!")
    except subprocess.CalledProcessError as e:
        logging.error(f"Gagal auto deploy: {e}")
    except Exception as e:
        logging.error(f"Error lain saat auto deploy: {e}")

if __name__ == "__main__":
    from utils import setup_logging
    setup_logging()
    update_all()