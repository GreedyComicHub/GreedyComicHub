import logging
import os
from scraper import scrape_comic_details, get_comic_id_and_display_name
from utils import read_json, write_json, upload_to_cloudinary, DATA_DIR

def add_comic(url):
    logging.info(f"Menambahkan komik baru: {url}")
    comic_id, _ = get_comic_id_and_display_name(url)
    title, author, synopsis, cover_url, soup, genre, comic_type = scrape_comic_details(url)
    if not title:
        logging.error("Gagal mendapatkan detail komik.")
        return

    cover_cloudinary_url = cover_url
    if cover_url:
        try:
            cover_cloudinary_url = upload_to_cloudinary(cover_url, comic_id, "cover")
            logging.info(f"Cover diupload ke Cloudinary: {cover_cloudinary_url}")
        except Exception as e:
            logging.error(f"Gagal upload cover ke Cloudinary: {e}")
            logging.info(f"Fallback ke URL asli untuk cover: {cover_cloudinary_url}")

    comic_data = {
        "title": title,
        "author": author,
        "synopsis": synopsis,
        "cover": cover_cloudinary_url,
        "genre": genre,
        "type": comic_type,
        "chapters": {},
        "source_url": url.strip()  # Simpen URL asli, bersihin spasi
    }

    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if os.path.exists(comic_file):
        existing_data = read_json(comic_file)
        comic_data["chapters"] = existing_data.get("chapters", {})
        comic_data["source_url"] = existing_data.get("source_url", url.strip())
        logging.info(f"Komik sudah ada, mempertahankan chapters dan source_url.")

    write_json(comic_file, comic_data)
    logging.info(f"Berhasil simpan data komik ke {comic_file}")
    update_index(comic_id, comic_data)

def update_index(comic_id, comic_data):
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    index_data[comic_id] = {
        "title": comic_data["title"],
        "synopsis": comic_data["synopsis"],
        "cover": comic_data["cover"],
        "genre": comic_data["genre"],
        "type": comic_data["type"],
        "total_chapters": len(comic_data["chapters"]),
        "source_url": comic_data["source_url"]  # Pastiin URL disimpan
    }
    write_json(index_file, index_data)
    logging.info(f"Berhasil update indeks di {index_file}")