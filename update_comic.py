"""Update comic data."""
import logging
from typing import Dict
from scraper import scrape_comic_data, scrape_chapter_images
from utils import read_json, write_json, get_comic_id_from_url, git_push, add_to_queue

def update_comic(comic_url: str, start_chapter: int = None, end_chapter: int = None) -> None:
    """Update comic metadata and chapters."""
    logging.info(f"Updating comic: {comic_url}")
    try:
        comic_id, _ = get_comic_id_from_url(comic_url)
        if not comic_id:
            raise ValueError("Invalid comic URL")

        # Load existing data
        comic_file = f"data/{comic_id}.json"
        existing_data = read_json(comic_file) or {}
        comic_data = scrape_comic_data(comic_url)
        comic_data["chapters"] = existing_data.get("chapters", {})

        # Scrape chapters if specified
        if start_chapter is not None and end_chapter is not None:
            logging.info(f"Scraping chapters {start_chapter} to {end_chapter} for {comic_id}")
            for chapter_num in range(start_chapter, end_chapter + 1):
                chapter_url = f"{comic_url.rstrip('/')}/chapter-{chapter_num}"
                images = scrape_chapter_images(chapter_url)
                if images:
                    comic_data["chapters"][str(chapter_num)] = {
                        "url": chapter_url,
                        "images": images
                    }
                    logging.info(f"Updated chapter {chapter_num} for {comic_id}")
                else:
                    logging.warning(f"No images found for chapter {chapter_num}")

        # Save to comic JSON
        write_json(comic_file, comic_data)

        # Update index.json
        index_file = "data/index.json"
        index_data = read_json(index_file) or {}
        index_data[comic_id] = {
            "title": comic_data["title"],
            "synopsis": comic_data["synopsis"],
            "cover": comic_data["cover"],
            "genre": comic_data["genre"],
            "type": comic_data["type"],
            "total_chapters": len(comic_data["chapters"]),
            "url": comic_url
        }
        write_json(index_file, index_data)
        logging.info(f"Updated index.json for {comic_id}")

        git_push()
        add_to_queue("comic_update", {"comic_id": comic_id, "url": comic_url})
        logging.info(f"Update selesai: {comic_url}")
    except Exception as e:
        logging.error(f"Error updating comic {comic_url}: {str(e)}")
        raise

def update_all_comics() -> None:
    """Update all comics in index.json."""
    logging.info("Updating all comics")
    try:
        index_file = "data/index.json"
        index_data = read_json(index_file) or {}
        for comic_id, comic_info in index_data.items():
            comic_url = comic_info.get("url")
            if not comic_url:
                logging.warning(f"No URL found for {comic_id}, skipping")
                continue
            # Cek chapter terbaru
            existing_data = read_json(f"data/{comic_id}.json") or {}
            current_chapters = existing_data.get("chapters", {})
            if not current_chapters:
                logging.info(f"No chapters found for {comic_id}, skipping")
                continue
            # Handle desimal chapters
            try:
                chapter_numbers = []
                for c in current_chapters.keys():
                    try:
                        chapter_numbers.append(float(c))
                    except ValueError:
                        logging.warning(f"Invalid chapter number {c} for {comic_id}, skipping")
                        continue
                if not chapter_numbers:
                    logging.info(f"No valid chapters for {comic_id}, skipping")
                    continue
                last_chapter = max(chapter_numbers)
                next_chapter = int(last_chapter) + 1 if last_chapter.is_integer() else int(last_chapter + 1)
                logging.info(f"Checking updates for {comic_id}, last chapter: {last_chapter}, next: {next_chapter}")
                # Cek 1 chapter ke depan
                update_comic(comic_url, start_chapter=next_chapter, end_chapter=next_chapter)
            except Exception as e:
                logging.error(f"Error processing chapters for {comic_id}: {str(e)}")
                continue
        logging.info("Update all comics selesai")
    except Exception as e:
        logging.error(f"Error updating all comics: {str(e)}")
        raise