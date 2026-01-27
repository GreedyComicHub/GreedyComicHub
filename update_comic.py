import os
import logging
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import fetch_page, read_json, write_json, DATA_DIR, get_comic_id_from_url
from scraper import scrape_chapter_images

def update_comic(url: str, start: float, end: float, overwrite: bool = False) -> Optional[bool]:
    """Update comic chapters in range.
    
    Args:
        url: Comic source URL.
        start: Start chapter number.
        end: End chapter number.
        overwrite: Whether to overwrite existing chapters.
        
    Returns:
        True on success, None on failure.
    """
    logging.info(f"Mulai update: {url}")
    comic_id = get_comic_id_from_url(url)
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    comic_data = read_json(comic_file)
    if not comic_data:
        logging.error(f"File {comic_file} ga ada, bro!")
        return

    html = fetch_page(url)
    if not html:
        logging.error(f"Gagal ambil halaman {url}")
        return

    try:
        soup = BeautifulSoup(html, 'html.parser')
        chapter_list = soup.select('td.judulseries a, table tr a:has(span)')
        logging.info(f"Found {len(chapter_list)} chapter links")

        # Kumpulin chapter dulu
        chapter_data = []
        for chapter in chapter_list:
            chapter_url = chapter.get('href', '').strip()
            if not chapter_url:
                continue
            if chapter_url.startswith('/'):
                chapter_url = urljoin(url, chapter_url)
            chapter_text = chapter.find('span').text.strip() if chapter.find('span') else chapter.text.strip()

            try:
                chapter_num = chapter_text.lower().replace('chapter ', '').replace('bab ', '').strip()
                chapter_num = float(chapter_num)
                chapter_num = int(chapter_num) if chapter_num.is_integer() else chapter_num
                if start <= chapter_num <= end:
                    chapter_data.append((chapter_num, chapter_text, chapter_url))
            except (ValueError, IndexError):
                logging.warning(f"Ga bisa parse chapter number dari: {chapter_text}")
                continue

        # Urutkan ascending berdasarkan chapter_num
        chapter_data.sort(key=lambda x: x[0])
        logging.info(f"Sorted {len(chapter_data)} chapters from {start} to {end}")

        chapters = {}
        for chapter_num, chapter_text, chapter_url in chapter_data:
            # Cek key "1", "1.0", "1.00", dll
            chapter_keys = [str(chapter_num), str(float(chapter_num)), f"{float(chapter_num):.1f}", f"{float(chapter_num):.2f}"]
            existing_chapter = {}
            for key in chapter_keys:
                if key in comic_data.get('chapters', {}):
                    existing_chapter = comic_data.get('chapters', {}).get(key, {})
                    logging.info(f"Found existing chapter {chapter_num} with key {key}")
                    break

            if existing_chapter.get('images') and all(img and img.startswith('http') for img in existing_chapter.get('images', [])) and not overwrite:
                logging.info(f"Chapter {chapter_num} sudah ada gambar, skip scraping")
                chapters[str(chapter_num)] = existing_chapter
                continue

            # Scrape gambar langsung dari URL asli
            images = scrape_chapter_images(chapter_url)
            logging.info(f"Scraped {len(images)} images for Chapter {chapter_num}")

            chapters[str(chapter_num)] = {
                "title": chapter_text,
                "url": chapter_url,
                "images": images
            }

        logging.info(f"Filtered {len(chapters)} chapters in range {start} to {end}")

        comic_data["chapters"] = comic_data.get("chapters", {})
        if overwrite:
            comic_data["chapters"].update(chapters)
        else:
            for num, chapter in chapters.items():
                comic_data["chapters"][num] = chapter
        comic_data["total_chapters"] = len(comic_data["chapters"])

        write_json(comic_file, comic_data)
        logging.info(f"Berhasil disimpan ke {comic_file}")

        index_file = os.path.join(DATA_DIR, "index.json")
        index_data = read_json(index_file) or {}
        if comic_id in index_data:
            index_data[comic_id]["total_chapters"] = comic_data["total_chapters"]
            write_json(index_file, index_data)
            logging.info(f"Updated {comic_id} in {index_file}")
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return None
    return True