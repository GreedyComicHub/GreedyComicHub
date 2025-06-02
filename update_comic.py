import logging
import os
from scraper import scrape_chapter_list, scrape_chapter_images
from utils import read_json, write_json_lock, fetch_page, upload_to_cloudinary, DATA_DIR
from bs4 import BeautifulSoup

def update_comic(url, start_chapter, end_chapter, overwrite=False):
    logging.info(f"Update {url} dari chapter {start_chapter} ke {end_chapter}")
    comic_id = url.split("/")[-1] or url.split("/")[-2]
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    index_file = os.path.join(DATA_DIR, "index.json")
    
    comic_data = read_json(comic_file) or {"chapters": {}}
    index_data = read_json(index_file) or {}
    
    html = fetch_page(url)
    if not html:
        logging.error(f"Gagal ambil {url}")
        return
    soup = BeautifulSoup(html, "html.parser")
    chapters = scrape_chapter_list(url, soup)
    
    for chapter_num in [str(float(n)) for n in range(int(start_chapter), int(end_chapter) + 1)]:
        if chapter_num in comic_data["chapters"] and not overwrite:
            logging.info(f"Chapter {chapter_num} udah ada, skip.")
            continue
        if chapter_num not in chapters:
            logging.warning(f"Chapter {chapter_num} nggak ada di web.")
            continue
            
        chapter_url = chapters[chapter_num]["url"]
        images = scrape_chapter_images(chapter_url)
        if not images:
            logging.error(f"Gagal ambil gambar untuk chapter {chapter_num}")
            continue
            
        cloudinary_urls = []
        for img_url in images:
            cloud_url = upload_to_cloudinary(img_url)
            if cloud_url:
                cloudinary_urls.append(cloud_url)
                
        comic_data["chapters"][chapter_num] = {
            "url": chapter_url,
            "pages": cloudinary_urls,
            "date_updated": chapters[chapter_num]["date"]
        }
        logging.info(f"Berhasil update chapter {chapter_num}")
        
    write_json_lock(comic_file, comic_data)
    
    if comic_id in index_data:
        index_data[comic_id]["total_chapters"] = len(comic_data["chapters"])
        write_json_lock(index_file, index_data)