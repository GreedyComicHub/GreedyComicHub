from utils import read_json, write_json, add_to_queue
import logging

def update_source_domain(old_domain, new_domain):
    logging.info(f"Mengganti domain dari {old_domain} ke {new_domain}")
    index_file = "data/index.json"
    index_data = read_json(index_file)
    updated_comics = []

    for comic_id in index_data:
        comic_file = f"data/{comic_id}.json"
        comic_data = read_json(comic_file)
        if comic_data.get("cover", "").startswith(f"https://{old_domain}"):
            comic_data["cover"] = comic_data["cover"].replace(f"https://{old_domain}", f"https://{new_domain}")
            write_json(comic_file, comic_data)
            index_data[comic_id]["cover"] = comic_data["cover"]
            updated_comics.append(comic_id)

    if updated_comics:
        write_json(index_file, index_data)
        add_to_queue("source_update", {"type": "domain", "old": old_domain, "new": new_domain, "comics": updated_comics})
    logging.info(f"Domain updated for comics: {updated_comics}")