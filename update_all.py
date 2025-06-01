from utils import read_json, add_to_queue
import logging
import requests

def update_all_comics():
    logging.info("Mulai update semua komik")
    index_file = "data/index.json"
    index_data = read_json(index_file)
    failed_urls = []

    for comic_id in index_data:
        comic_file = f"data/{comic_id}.json"
        comic_data = read_json(comic_file)
        source_url = f"https://komiku.org/manga/{comic_id}"  # Asumsi default
        try:
            response = requests.head(source_url)
            if response.status_code == 200:
                add_to_queue("comic_update", {"comic_id": comic_id, "url": source_url})
            else:
                failed_urls.append((comic_id, source_url))
        except:
            failed_urls.append((comic_id, source_url))

    if failed_urls:
        logging.warning("Komik yang gagal diakses:")
        for comic_id, url in failed_urls:
            logging.warning(f"{comic_id}: {url}")
    logging.info("Update semua komik selesai")