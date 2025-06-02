import logging
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
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    index_data[comic_id] = {
        "title": comic_data["title"],
        "synopsis": comic_data["synopsis"],
        "cover": comic_data["cover"],
        "genre": comic_data["genre"],
        "type": comic_data["type"],
        "total_chapters": len(comic_data["chapters"])
    }
    write_json(index_file, index_data)