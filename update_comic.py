import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import fetch_page, read_json, write_json, DATA_DIR, get_comic_id_from_url, upload_to_cloudinary

def update_comic(url, start, end, overwrite=False):
    logging.info(f"Mulai update: {url}")
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
        chapter_list = soup.select('td.judulseries a, table tr a:has(span)')  # Fallback selector
        logging.info(f"Found {len(chapter_list)} chapter links")

        chapters = {}
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
                    # Cek apakah chapter sudah ada dan punya gambar
                    existing_chapter = comic_data.get('chapters', {}).get(str(chapter_num), {})
                    if existing_chapter.get('images') and not overwrite:
                        logging.info(f"Chapter {chapter_num} sudah ada gambar, skip upload")
                        chapters[str(chapter_num)] = existing_chapter
                        continue

                    # Scrape gambar dari halaman chapter
                    chapter_html = fetch_page(chapter_url)
                    images = []
                    if chapter_html:
                        chapter_soup = BeautifulSoup(chapter_html, 'html.parser')
                        image_elements = chapter_soup.select('div#Baca_Komik img[itemprop="image"]')
                        for img in image_elements:
                            img_url = img.get('src', '').strip()
                            if img_url and img_url.startswith('http'):
                                if img_url in existing_chapter.get('images', []) and not overwrite:
                                    logging.info(f"Gambar sudah ada untuk Chapter {chapter_num}: {img_url}")
                                    images.append(img_url)
                                else:
                                    cloudinary_url = upload_to_cloudinary(img_url, comic_id, str(chapter_num))
                                    images.append(cloudinary_url)
                        logging.info(f"Scraped {len(images)} images for Chapter {chapter_num}")
                    else:
                        logging.warning(f"Gagal ambil halaman chapter {chapter_url}")

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

        # Update index.json
        index_file = os.path.join(DATA_DIR, "index.json")
        index_data = read_json(index_file) or {}
        if comic_id in index_data:
            index_data[comic_id]["total_chapters"] = comic_data["total_chapters"]
            write_json(index_file, index_data)
            logging.info(f"Updated {comic_id} in {index_file}")
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")