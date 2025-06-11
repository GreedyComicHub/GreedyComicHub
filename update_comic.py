import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import fetch_page, read_json, write_json, DATA_DIR, get_comic_id_from_url, upload_to_cloudinary

def update_comic(url, start, end, overwrite=False):
    logging.info(f"Mulai update chapter: {url}")
    comic_id = get_comic_id_from_url(url)
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    comic_data = read_json(comic_file)
    if not comic_data:
        logging.error(f"File {comic_file} ga ada, bro!")
        return

    # Scrape daftar chapter
    html = fetch_page(url)
    if not html:
        logging.error(f"Gagal ambil halaman {url}")
        return

    try:
        soup = BeautifulSoup(html, 'html.parser')
        chapter_list = soup.select('td.judulseries a')
        logging.info(f"Found {len(chapter_list)} chapter links")

        chapters = {}
        for chapter in chapter_list:
            chapter_url = chapter.get('href')
            if chapter_url.startswith('/'):
                chapter_url = urljoin(url, chapter_url)
            chapter_text = chapter.find('span').text.strip() if chapter.find('span') else chapter.text.strip()
            logging.info(f"Chapter: {chapter_text}, URL: {chapter_url}")

            try:
                chapter_num = chapter_text.lower().replace('chapter ', '').replace('bab ', '').strip()
                chapter_num = float(chapter_num)
                if start <= chapter_num <= end:
                    # Scrape gambar dari halaman chapter
                    chapter_html = fetch_page(chapter_url)
                    images = []
                    if chapter_html:
                        chapter_soup = BeautifulSoup(chapter_html, 'html.parser')
                        image_elements = chapter_soup.select('div#Baca_Komik img[itemprop="image"]')
                        for img in image_elements:
                            img_url = img.get('src')
                            if img_url and img_url.startswith('http'):
                                cloudinary_url = upload_to_cloudinary(img_url, comic_id, str(chapter_num))
                                images.append(cloudinary_url)
                        logging.info(f"Scraped {len(images)} images for Chapter {chapter_num}")

                    chapters[str(chapter_num)] = {
                        "title": chapter_text,
                        "url": chapter_url,
                        "images": images
                    }
            except (ValueError, IndexError):
                logging.warning(f"Ga bisa parse chapter number dari: {chapter_text}")
                continue

        logging.info(f"Filtered {len(chapters)} chapters in range {start} to {end}")

        # Update comic data
        comic_data["chapters"] = comic_data.get("chapters", {})
        if overwrite:
            comic_data["chapters"].update(chapters)
        else:
            for num, chapter in chapters.items():
                if num not in comic_data["chapters"]:
                    comic_data["chapters"][num] = chapter
        comic_data["total_chapters"] = len(comic_data["chapters"])

        write_json(comic_file, comic_data)
        logging.info(f"Berhasil disimpan ke {comic_file}")
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")