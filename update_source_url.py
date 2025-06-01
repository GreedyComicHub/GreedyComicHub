from utils import read_json, write_json, add_to_queue
import logging

def update_source_url(old_url, new_url):
    logging.info(f"Mengganti URL dari {old_url} ke {new_url}")
    comic_id, _ = get_comic_id_from_url(old_url)
    new_comic_id, _ = get_comic_id_from_url(new_url)
    
    if not comic_id or comic_id != new_comic_id:
        logging.error("Comic ID tidak cocok atau URL tidak valid")
        return

    comic_file = f"data/{comic_id}.json"
    comic_data = read_json(comic_file)
    index_file = "data/index.json"
    index_data = read_json(index_file)

    if comic_data.get("cover") == old_url:
        comic_data["cover"] = new_url
        write_json(comic_file, comic_data)
        index_data[comic_id]["cover"] = new_url
        write_json(index_file, index_data)
        add_to_queue("source_update", {"type": "url", "comic_id": comic_id, "old": old_url, "new": new_url})
        logging.info(f"Updated URL for {comic_id}")