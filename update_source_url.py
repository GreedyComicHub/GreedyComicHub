import logging
import os
from utils import read_json, write_json_lock, push_to_git, DATA_DIR

def update_source_url(old_url, new_url):
    logging.info(f"Ganti {old_url} ke {new_url}...")
    changes_m = False

    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    index_changed = False
    if index_data:
        for comic_id, info in index_data.items():
            if "source_url" in info and old_url in info["source_url"]:
                info["source_url"] = info["source_url"].replace(old_url, new_url)
                logging.info(f"Update source_url {comic_id}: {old_url} -> {info['source_url']}")
                index_changed = True
                changes_m = True
        if index_changed:
            write_json_lock(index_file, index_data)
            logging.info(f"Simpan {index_file}")

    for comic_id in index_data:
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.warning(f"{comic_file} not found.")
            continue
        comic_data = read_json(comic_file)
        file_changed = False
        
        if "chapters" in comic_data:
            for chapter_num, chapter in comic_data["chapters"].items():
                if "url" in chapter and old_url in chapter["url"]:
                    chapter["url"] = chapter["url"].replace(old_url, new_url)
                    logging.info(f"Update chapter url {chapter_num}: {old_url} -> {chapter['url']}")
                    file_changed = True
                        
        if file_changed:
            write_json_lock(comic_file, comic_data)
            logging.info(f"Simpan {comic_file}")
            changes_m = True

    if changes_m:
        push_to_git()