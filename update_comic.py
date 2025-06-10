import logging
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import fetch_page, upload_to_cloudinary, read_json, write_json, DATA_DIR

def update_comic(url, start_chapter, end_chapter, overwrite=False):
    """Update chapter komik dari start_chapter hingga end_chapter."""
    logging.info(f"Update komik {url} dari chapter {start_chapter} ke {end_chapter}, overwrite: {overwrite}")
    
    html_content = fetch_page(url)
    if not html_content:
        logging.error(f"Gagal mengambil halaman {url}")
        return
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Ambil judul untuk comic_id
    title_element = soup.select_one("h1[itemprop='name']")
    title = title_element.text.strip() if title_element else "Unknown Title"
    comic_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    
    # Load data komik
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    comic_data = read_json(comic_file)
    if not comic_data:
        logging.error(f"Komik {comic_id} tidak ditemukan di {comic_file}")
        return
    
    # Pastikan source_url tetap ada
    comic_data["source_url"] = url
    
    # Ambil daftar chapter
    chapter_list = soup.select("div#chapter_list a")
    chapters_to_update = []
    for chapter in chapter_list:
        chapter_title = chapter.text.strip()
        chapter_url = chapter["href"]
        match = re.search(r'chapter[\s-]?(\d+\.?\d*)', chapter_title.lower())
        if match:
            chapter_num = float(match.group(1))
            if start_chapter <= chapter_num <= end_chapter:
                chapters_to_update.append((chapter_num, chapter_title, chapter_url))
    
    chapters_updated = False
    for chapter_num, chapter_title, chapter_url in chapters_to_update:
        chapter_key = f"{chapter_num:.1f}"
        if chapter_key in comic_data["chapters"] and not overwrite:
            logging.info(f"Chapter {chapter_key} sudah ada, skip.")
            continue
        
        chapter_html = fetch_page(chapter_url)
        if not chapter_html:
            logging.error(f"Gagal mengambil chapter {chapter_url}")
            continue
        
        chapter_soup = BeautifulSoup(chapter_html, "html.parser")
        image_elements = chapter_soup.select("img[itemprop='image']")
        image_urls = []
        for img in image_elements:
            img_url = img["src"] if img else ""
            if img_url:
                img_url = upload_to_cloudinary(img_url, comic_id, chapter_key)
                image_urls.append(img_url)
        
        comic_data["chapters"][chapter_key] = {
            "title": chapter_title,
            "url": chapter_url,
            "images": image_urls
        }
        chapters_updated = True
        logging.info(f"Chapter {chapter_key} berhasil diupdate untuk komik {comic_id}")
    
    # Update total_chapters
    comic_data["total_chapters"] = len(comic_data["chapters"])
    
    # Simpan ke file komik
    write_json(comic_file, comic_data)
    
    # Update index.json
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    index_data[comic_id] = {
        "title": comic_data["title"],
        "synopsis": comic_data["synopsis"],
        "cover": comic_data["cover"],
        "genre": comic_data["genre"],
        "type": comic_data["type"],
        "total_chapters": comic_data["total_chapters"],
        "source_url": url  # Pastikan source_url disimpan
    }
    write_json(index_file, index_data)
    
    if chapters_updated:
        logging.info(f"Komik {comic_id} berhasil diupdate.")
    else:
        logging.info(f"Tidak ada chapter baru untuk komik {comic_id}.")