import logging
import os
import json
from utils import read_json, write_json, setup_logging, push_to_github, DATA_DIR

setup_logging()

def fix_index():
    logging.info("Memulai perbaikan index.json...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = {}

    # Mapping comic_id ke source_url (bisa ditambah manual kalau perlu)
    url_mapping = {
        "one-punch-man": "https://komiku.org/manga/manga-one-punch-man",
        "komik-one-piece-indo": "https://komiku.org/manga/manga-komik-one-piece-indo"
        # Tambah komik lain di sini kalau perlu
    }

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json") and filename != "index.json":
            comic_id = filename.replace(".json", "")
            file_path = os.path.join(DATA_DIR, filename)
            comic_data = read_json(file_path)

            if not comic_data or not comic_data.get("title"):
                logging.warning(f"File {file_path} invalid atau kosong, dilewati.")
                continue

            index_data[comic_id] = {
                "title": comic_data.get("title", "Unknown"),
                "synopsis": comic_data.get("synopsis", "No synopsis"),
                "cover": comic_data.get("cover", ""),
                "genre": comic_data.get("genre", "Unknown"),
                "type": comic_data.get("type", "Unknown"),
                "total_chapters": len(comic_data.get("chapters", {})),
                "source_url": url_mapping.get(comic_id, f"https://komiku.org/manga/manga-{comic_id}")
            }
            logging.info(f"Menambahkan komik ke index: {comic_id}")

    write_json(index_file, index_data)
    logging.info(f"Berhasil menyimpan index.json ke {index_file}")
    push_to_github()
    logging.info("Perbaikan index.json selesai!")

if __name__ == "__main__":
    fix_index()