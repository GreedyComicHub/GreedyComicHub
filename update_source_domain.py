import logging
import os
from utils import read_json, write_json, DATA_DIR

def update_source_domain(old_domain, new_domain):
    logging.info(f"Mengganti domain dari {old_domain} ke {new_domain}...")
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json") and filename != "index.json":
            file_path = os.path.join(DATA_DIR, filename)
            data = read_json(file_path)
            updated = False
            if data.get("cover", "").startswith(f"https://{old_domain}"):
                data["cover"] = data["cover"].replace(old_domain, new_domain)
                updated = True
            for chapter in data.get("chapters", {}).values():
                for i, page in enumerate(chapter.get("pages", [])):
                    if page.startswith(f"https://{old_domain}"):
                        chapter["pages"][i] = page.replace(old_domain, new_domain)
                        updated = True
            if updated:
                write_json(file_path, data)
                logging.info(f"Domain diperbarui di {file_path}")