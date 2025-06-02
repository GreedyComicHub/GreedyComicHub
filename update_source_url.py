import logging
import os
from utils import read_json, write_json, DATA_DIR

def update_source_url(old_url, new_url):
    logging.info(f"Mengganti URL dari {old_url} ke {new_url}...")
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json") and filename != "index.json":
            file_path = os.path.join(DATA_DIR, filename)
            data = read_json(file_path)
            updated = False
            if data.get("cover") == old_url:
                data["cover"] = new_url
                updated = True
            for chapter in data.get("chapters", {}).values():
                for i, page in enumerate(chapter.get("pages", [])):
                    if page == old_url:
                        chapter["pages"][i] = new_url
                        updated = True
            if updated:
                write_json(file_path, data)
                logging.info(f"URL diperbarui di {file_path}")