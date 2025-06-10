import logging
import os
import re
from bs4 import BeautifulSoup
from utils import fetch_page, paraphrase_synopsis, upload_to_cloudinary, read_json, write_json, DATA_DIR

def add_comic(url):
    logging.info(f"Menambahkan komik: {url}")
    
    html_content = fetch_page(url)
    if not html_content:
        logging.error(f"Gagal mengambil {url}")
        return
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Judul
    title_element = soup.select_one("h1[itemprop='name']") or soup.select_one("h1.judul")
    title = title_element.text.strip() if title_element else "Unknown Title"
    if title == "Unknown Title":
        logging.error("Gagal ambil judul")
    
    # Sinopsis
    synopsis_element = soup.select_one("div[itemprop='description']") or soup.select_one("div.komik_info-description-sinopsis")
    synopsis = synopsis_element.text.strip() if synopsis_element else "No synopsis available."
    synopsis = paraphrase_synopsis(synopsis)
    
    # Cover
    cover_element = soup.select_one("img[itemprop='image']") or soup.select_one("img.komik_info-cover-image")
    cover_url = cover_element["src"] if cover_element else ""
    comic_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    if cover_url:
        cover_url = upload_to_cloudinary(cover_url, comic_id, "cover")
    
    # Genre
    genre_elements = soup.select("td:contains('Genre') + td a") or soup.select("div.komik_info-genre a")
    genre = ", ".join([g.text.strip() for g in genre_elements]) if genre_elements else "Unknown Genre"
    
    # Tipe
    type_element = soup.select_one("td:contains('Type') + td") or soup.select_one("td:contains('Jenis Komik') + td")
    comic_type = type_element.text.strip() if type_element else "Unknown Type"
    
    # Author
    author_element = soup.select_one("td:contains('Author') + td") or soup.select_one("div.komik_info-author")
    author = author_element.text.strip() if author_element else "Unknown Author"
    
    comic_data = {
        "title": title,
        "synopsis": synopsis,
        "cover": cover_url,
        "genre": genre,
        "type": comic_type,
        "author": author,
        "chapters": {},
        "total_chapters": 0,
        "source_url": url
    }
    
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    write_json(comic_file, comic_data)
    
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    if not isinstance(index_data, dict):
        index_data = {}
    index_data[comic_id] = {
        "title": title,
        "synopsis": synopsis,
        "cover": cover_url,
        "genre": genre,
        "type": comic_type,
        "author": author,
        "total_chapters": 0,
        "source_url": url
    }
    write_json(index_file, index_data)
    
    logging.info(f"Komik {title} ditambahkan, ID: {comic_id}")