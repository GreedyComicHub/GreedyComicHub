"""Update comic data."""
import logging
import requests
from typing import Dict, List
from scraper import scrape_comic_data, scrape_chapter_images
from utils import read_json, write_json, get_comic_id_from_url, git_push, add_to_queue

def format_chapter_url(base_url: str, chapter_num: float) -> str:
    """Format chapter URL with leading zero or decimal."""
    comic_id = base_url.split('/')[-1]
    if chapter_num.is_integer():
        return f"https://komiku.org/chapters/{comic_id}-chapter-{int(chapter_num):02d}"
    else:
        int_part = int(chapter_num)
        dec_part = int((chapter_num - int_part) * 10)
        return f"https://komiku.org/chapters/{comic_id}-chapter-{int-part}-{dec-part}"

def update_comic(comic_url: str, start_chapter: int = None, end_chapter: int = None) -> None:
    """Update comic metadata and chapters."""
    logging.info(f"Updating comic: {comic_url}")
    success = False
    try:
        comic_id, _ = get_comic_id_from_url(comic_url)
        if not comic_id:
            raise ValueError("Invalid comic URL")

        # Validasi URL
        try:
            response = requests.head(comic_url, timeout=5, allow_redirects=True)
            if response.status_code != 200:
                logging.error(f"URL {comic_url} tidak valid, status code: {response.status_code}")
                raise ValueError(f"Invalid URL: {comic_url}")
        except Exception as e:
            logging.error(f"Error accessing URL {comic_url}: {str(e)}")
            raise

        # Load existing data
        comic_file = f"data/{comic_id}.json"
        existing_data = read_json(comic_file) or {}
        comic_data = scrape_comic_data(comic_url)
        comic_data["chapters"] = existing_data.get("chapters", {})

        # Scrape chapters if specified
        if start_chapter is not None and end_chapter is not None:
            logging.info(f"Adding chapters {start_chapter} to {end_chapter} for {comic_id}")
            for chapter_num in range(start_chapter, end_chapter + 1):
                chapter_url = format_chapter_url(comic_url, chapter_num)
                logging.info(f"Generated chapter URL: {chapter_url}")
                try:
                    images = scrape_chapter_images(chapter_url)
                    if images and all("thumbnail" not in img for img in images):
                        comic_data["chapters"][str(chapter_num)] = {
                            "url": chapter_url,
                            "images": images
                        }
                        logging.info(f"Added chapter {chapter_num} for {comic_id} with {len(images)} images")
                        success = True
                    else:
                        logging.warning(f"No valid images found for chapter {chapter_num} at {chapter_url}, skipping")
                        continue
                except Exception as e:
                    logging.error(f"Error adding chapter {chapter_num} for {comic_id}: {str(e)}")
                    continue

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
        logging.info(f"Updated index.json for {comic_id} with {len(comic_data['chapters'])} chapters")

        git_push()
        if success:
            add_to_queue("comic_update", {"comic_id": comic_id, "url": comic_url})
            logging.info(f"Added to queue: comic_update for {comic_id}")
        else:
            logging.warning(f"Skipped queue for {comic_id} due to no successful chapter updates")
        logging.info(f"Update completed for {comic_url}")
    except Exception as e:
        logging.error(f"Error updating comic {comic_url}: {str(e)}")
        raise

def update_all_comics() -> None:
    """Update all comics in index.json."""
    logging.info("Starting update for all comics")
    error_list: List[str] = []
    try:
        index_file = "data/index.json"
        index_data = read_json(index_file) or {}
        if not index_data:
            logging.warning("No comics found in index.json")
            return

        for comic_id, comic_info in index_data.items():
            comic_url = comic_info.get("url")
            if not comic_url:
                error_msg = f"No URL found for {comic_id}"
                logging.warning(error_msg)
                error_list.append(error_msg)
                continue

            # Load existing data
            comic_file = f"data/{comic_id}.json"
            existing_data = read_json(comic_file) or {}
            current_chapters = existing_data.get("chapters", {})
            if not current_chapters:
                logging.info(f"No chapters found for {comic_id}, skipping")
                continue

            # Handle integer and decimal chapters
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
                next_chapters = []
                if last_chapter.is_integer():
                    next_chapters = [last_chapter + 0.5, last_chapter + 1]
                else:
                    next_chapters = [int(last_chapter) + 1]
                logging.info(f"Checking {comic_id}, last chapter: {last_chapter}, trying {next_chapters}")

                # Cek next chapters
                success = False
                for next_chapter in next_chapters:
                    chapter_url = format_chapter_url(comic_url, next_chapter)
                    try:
                        images = scrape_chapter_images(chapter_url)
                        if images and all("thumbnail" not in img for img in images):
                            existing_data["chapters"][str(next_chapter)] = {
                                "url": chapter_url,
                                "images": images
                            }
                            write_json(comic_file, existing_data)
                            index_data[comic_id]["total_chapters"] = len(existing_data["chapters"])
                            write_json(index_file, index_data)
                            git_push()
                            logging.info(f"Added chapter {next_chapter} for {comic_id} with {len(images)} images")
                            success = True
                        else:
                            logging.info(f"No new chapters for {comic_id} at {chapter_url}")
                    except Exception as e:
                        error_msg = f"Failed to update {comic_id} chapter {next_chapter}: {str(e)}"
                        logging.error(error_msg)
                        error_list.append(error_msg)

                if success:
                    add_to_queue("comic_update", {"comic_id": comic_id, "url": comic_url})
                    logging.info(f"Added to queue: comic_update for {comic_id}")

            except Exception as e:
                error_msg = f"Error processing {comic_id}: {str(e)}"
                logging.error(error_msg)
                error_list.append(error_msg)

        logging.info("Completed update for all comics")
        if error_list:
            logging.info("Summary of errors:")
            for error in error_list:
                logging.info(f"- {error}")
    except Exception as e:
        logging.error(f"Error updating all comics: {str(e)}")

def change_comic_url(old_url: str, new_url: str) -> None:
    """Change comic URL in index.json."""
    logging.info(f"Changing URL from {old_url} to {new_url}")
    try:
        index_file = "data/index.json"
        index_data = read_json(index_file) or {}
        comic_id, _ = get_comic_id_from_url(old_url)
        if not comic_id:
            raise ValueError(f"Invalid old URL: {old_url}")

        new_comic_id, _ = get_comic_id_from_url(new_url)
        if comic_id != new_comic_id:
            raise ValueError(f"Comic ID mismatch: {comic_id} (old) vs {new_comic_id} (new)")

        for cid, info in index_data.items():
            if info.get("url") == old_url:
                index_data[cid]["url"] = new_url
                logging.info(f"Updated URL for {cid} to {new_url}")
                write_json(index_file, index_data)
                git_push()
                return
        logging.warning(f"URL {old_url} not found in index.json")
    except Exception as e:
        logging.error(f"Error changing URL from {old_url} to {new_url}: {str(e)}")
        raise