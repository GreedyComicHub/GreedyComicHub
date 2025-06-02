import logging
import os
from utils import read_json, write_json_lock, fetch_page, DATA_DIR
from bs4 import BeautifulSoup

def add_comic(url):
    logging.info(f"Menambahkan: {url}")
    comic_id = url.split("/")[-1] or url.split("/")[-2]
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    index_file = os.path.join(DATA_DIR, "index.json")
    
    html = fetch_page(url)
    if not html:
        logging.error(f"Gagal ambil {url}")
        return
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one("h1").text.strip() if soup.select_one("h1") else comic_id
    cover = soup.select_one("img.cover").get("src") if soup.select_one("img.cover") else ""
    synopsis = soup.select_one(".sin").text.strip() if soup.select_one(".sin") else ""
    genre = soup.select_one(".gen").text.strip() if soup.select_one(".gen") else "Unknown"
    comic_type = soup.select_one(".type").text.strip() or "Unknown"
    
    index_data = read_json(index_file) or {}
    index_data[comic_id] = {
        "source_url": url,
        "title": title,
        "cover": cover,
        "synopsis": synopsis,
        "genre": genre,
        "type": comic_type,
        "total_chapters": 0
    }
    write_json_lock(index_file, index_data)
    logging.info(f"Berhasil tambah {comic_id} ke index.json")
    
    comic_data = {
        "title": title,
        "cover": cover,
        "synopsis": synopsis,
        "genre": genre,
        "type": comic_type,
        "chapters": {}
    }
    write_json_lock(comic_file, comic_data)
    logging.info(f"Berhasil tambah {comic_file}")