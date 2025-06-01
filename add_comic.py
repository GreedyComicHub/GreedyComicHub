"""Add new comic to the system."""
import logging
from typing import Dict
from scraper import scrape_comic_data
from utils import read_json, write_json, add_to_queue, get_comic_id_from_url, git_push

def add_comic(comic_url: str) -> None:
    """Add a new comic from the given URL."""
    logging.info(f"Menambahkan komik baru: {comic_url}")
    try:
        comic_data = scrape_comic_data(comic_url)
        comic_id, _ = get_comic_id_from_url(comic_url)
        if not comic_id:
            raise ValueError("Invalid comic URL")

        # Save to comic JSON
        comic_file = f"data/{comic_id}.json"
        existing_data = read_json(comic_file) or {}
        if existing_data.get("chapters"):
            logging.info(f"Preserving {len(existing_data['chapters'])} chapters for {comic_id}")
        write_json(comic_file, comic_data)

        # Update index.json
        index_file = "data/index.json"
        index_data: Dict = read_json(index_file) or {}
        index_data[comic_id] = {
            "title": comic_data["title"],
            "synopsis": comic_data["synopsis"],
            "cover": comic_data["cover"],
            "genre": comic_data["genre"],
            "type": comic_data["type"],
            "total_chapters": len(comic_data["chapters"])
        }
        write_json(index_file, index_data)
        logging.info(f"Updated index.json for {comic_id} with {len(comic_data['chapters'])} chapters")

        # Push to GitHub
        git_push()

        # Add to queue
        add_to_queue("comic_add", {"comic_id": comic_id, "url": comic_url})
        logging.info(f"Penambahan komik selesai: {comic_url}")
    except Exception as e:
        logging.error(f"Error adding comic {comic_url}: {str(e)}")
        raise