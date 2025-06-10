import logging
import os
from utils import read_json, write_json, DATA_DIR

def update_source_url(old_url, new_url):
<<<<<<< HEAD
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
=======
    """Ganti source_url lama dengan yang baru di index.json dan file komik."""
    logging.info(f"Mengganti source_url dari {old_url} ke {new_url}")
    
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    
    comic_id_to_update = None
    for comic_id, comic_info in index_data.items():
        if comic_info.get("source_url") == old_url:
            comic_id_to_update = comic_id
            break
    
    if not comic_id_to_update:
        logging.error(f"URL {old_url} tidak ditemukan di index.json")
        return
    
    # Update index.json
    index_data[comic_id_to_update]["source_url"] = new_url
    write_json(index_file, index_data)
    
    # Update file komik
    comic_file = os.path.join(DATA_DIR, f"{comic_id_to_update}.json")
    if os.path.exists(comic_file):
        comic_data = read_json(comic_file)
        comic_data["source_url"] = new_url
        write_json(comic_file, comic_data)
        logging.info(f"Berhasil update source_url untuk komik {comic_id_to_update}")
    else:
        logging.error(f"File {comic_file} tidak ditemukan")
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
