from scraper import scrape_chapter_images
from utils import read_json, write_json, upload_image, add_to_queue, get_comic_id_from_url  # Tambah import
import requests
import logging
from bs4 import BeautifulSoup
import re  # Tambah import re

def update_comic(comic_url):
    logging.info(f"Mulai update chapter: {comic_url}")
    try:
        comic_id, _ = get_comic_id_from_url(comic_url)
        if not comic_id:
            raise ValueError("Invalid comic URL")

        comic_file = f"data/{comic_id}.json"
        comic_data = read_json(comic_file)
        if not comic_data:
            raise ValueError(f"Comic {comic_id} not found")

        # Ambil daftar chapter
        response = requests.get(comic_url)
        soup = BeautifulSoup(response.text, "html.parser")
        chapters = []
        for link in soup.find_all("a", href=True):
            if "/chapter-" in link["href"]:
                chapter_num = re.search(r"chapter-(\d+)", link["href"])
                if chapter_num:
                    chapters.append((chapter_num.group(1), link["href"]))

        chapters.sort(key=lambda x: int(x[0]))  # Urutkan

        new_chapters = {}
        for chapter_num, chapter_url in chapters[:1]:  # Batasi 1 chapter untuk contoh
            if chapter_num not in comic_data.get("chapters", {}):
                images = scrape_chapter_images(chapter_url)
                uploaded_images = []
                for img_url in images:
                    uploaded_url = upload_image(img_url, f"{comic_id}/chapter_{chapter_num}")
                    uploaded_images.append(uploaded_url)
                new_chapters[chapter_num] = {"pages": uploaded_images}
                logging.info(f"Added chapter {chapter_num} for {comic_id}")

        if new_chapters:
            comic_data["chapters"].update(new_chapters)
            write_json(comic_file, comic_data)
            index_file = "data/index.json"
            index_data = read_json(index_file)
            if comic_id in index_data:
                index_data[comic_id]["total_chapters"] = len(comic_data["chapters"])
                write_json(index_file, index_data)
            add_to_queue("comic_update", {"comic_id": comic_id, "chapters": list(new_chapters.keys())})

    except Exception as e:
        logging.error(f"Error updating comic {comic_url}: {str(e)}")
        raise