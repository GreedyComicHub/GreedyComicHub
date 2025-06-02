import logging
import os
from utils import read_json, write_json_lock, push_to_git, DATA_DIR

def update_source_domain(old_domain, new_domain, old_path=None, new_path=None):
    logging.info(f"Ganti {old_domain} ke {new_domain}...")
    changes_m = False

    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    index_changed = False
    if index_data:
        for comic_id, info in index_data.items():
            if "cover" in info and old_domain in info["cover"]:
                old_url = info["cover"]
                info["cover"] = old_url.replace(old_domain, new_domain)
                if old_path and new_path:
                    info["cover"] = info["cover"].replace(old_path, new_path)
                logging.info(f"Update cover {comic_id}: {old_url} -> {info['cover']}")
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
        
        if "cover" in comic_data and old_domain in comic_data["cover"]:
            old_url = comic_data["cover"]
            comic_data["cover"] = old_url.replace(old_domain, new_domain)
            if old_path and new_path:
                comic_data["cover"] = comic_data["cover"].replace(old_path, new_path)
            logging.info(f"Update cover {comic_file}: {old_url} -> {comic_data['cover']}")
            file_changed = True
            
        if "chapters" in comic_data:
            for chapter_num, chapter in comic_data["chapters"].items():
                for i, page in enumerate(chapter.get("pages", [])):
                    if old_domain in page:
                        old_page = page
                        chapter["pages"][i] = old_page.replace(old_domain, new_domain)
                        if old_path and new_path:
                            chapter["pages"][i] = chapter["pages"][i].replace(old_path, new_path)
                        logging.info(f"Update page {chapter_num}: {old_page} -> {chapter['pages'][i]}")
                        file_changed = True
                        
        if file_changed:
            write_json_lock(comic_file, comic_data)
            logging.info(f"Simpan {comic_file}")
            changes_m = True

    if changes_m:
        push_to_git()