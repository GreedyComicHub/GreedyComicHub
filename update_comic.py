import logging
<<<<<<< HEAD
import os
from scraper import scrape_chapter_list, scrape_chapter_images, get_comic_id_and_display_name
from utils import read_json, write_json, upload_to_cloudinary, fetch_page, DATA_DIR

def update_comic(url, start_chapter, end_chapter, overwrite=False):
    logging.info(f"Mulai update chapter: {url}")
    comic_id, _ = get_comic_id_and_display_name(url)
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if not os.path.exists(comic_file):
        logging.error(f"File {comic_file} tidak ada. Jalankan 'add-comic' dulu.")
        return
    comic_data = read_json(comic_file)
    html = fetch_page(url)
    if not html:
        logging.error("Gagal mengambil halaman komik.")
        return
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    chapters = scrape_chapter_list(url, soup)
    if not chapters:
        logging.error("Tidak ada chapter yang ditemukan.")
        return
    sorted_chapter_nums = sorted(chapters.keys(), key=lambda x: float(x))
    for chapter_num in sorted_chapter_nums:
        chapter_num_float = float(chapter_num)
        if start_chapter <= chapter_num_float <= end_chapter:
            if str(chapter_num) in comic_data["chapters"] and not overwrite:
                logging.info(f"Chapter {chapter_num} sudah ada, melewati.")
                continue
            image_urls = scrape_chapter_images(chapters[chapter_num])
            if not image_urls:
                continue
            uploaded_urls = []
            for img_url in image_urls:
                uploaded_url = upload_to_cloudinary(img_url, comic_id, chapter_num)
                uploaded_urls.append(uploaded_url)
            comic_data["chapters"][str(chapter_num)] = {"pages": uploaded_urls}
    comic_data["chapters"] = dict(sorted(comic_data["chapters"].items(), key=lambda x: float(x[0])))
    write_json(comic_file, comic_data)
    logging.info(f"Berhasil disimpan ke {comic_file}")
    update_index(comic_id, comic_data)

def update_index(comic_id, comic_data):
=======
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
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    index_data[comic_id] = {
        "title": comic_data["title"],
        "synopsis": comic_data["synopsis"],
        "cover": comic_data["cover"],
        "genre": comic_data["genre"],
        "type": comic_data["type"],
<<<<<<< HEAD
        "total_chapters": len(comic_data["chapters"])
    }
    write_json(index_file, index_data)
=======
        "total_chapters": comic_data["total_chapters"],
        "source_url": url  # Pastikan source_url disimpan
    }
    write_json(index_file, index_data)
    
    if chapters_updated:
        logging.info(f"Komik {comic_id} berhasil diupdate.")
    else:
        logging.info(f"Tidak ada chapter baru untuk komik {comic_id}.")
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
