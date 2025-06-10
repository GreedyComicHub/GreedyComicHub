import logging
import os
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