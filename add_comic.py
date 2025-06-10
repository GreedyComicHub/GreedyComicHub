import logging
import os
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import fetch_page, paraphrase_synopsis, upload_to_cloudinary, read_json, write_json, DATA_DIR

def add_comic(url):
    logging.info(f"Menambahkan komik dari URL: {url}")
    
    html_content = fetch_page(url)
    if not html_content:
        logging.error(f"Gagal mengambil halaman {url}")
        return
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Ambil judul
    title_element = soup.select_one("h1.judul") or soup.select_one("h1[itemprop='name']")
    title = title_element.text.strip() if title_element else "Unknown Title"
    
    # Ambil sinopsis
    synopsis_element = soup.select_one("div.komik_info-description-sinopsis") or soup.select_one("div[itemprop='description']")
    synopsis = synopsis_element.text.strip() if synopsis_element else "No synopsis available."
    synopsis = paraphrase_synopsis(synopsis)
    
    # Ambil cover
    cover_element = soup.select_one("img.komik_info-cover-image") or soup.select_one("img[itemprop='image']")
    cover_url = cover_element["src"] if cover_element else ""
    if cover_url:
        comic_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        cover_url = upload_to_cloudinary(cover_url, comic_id, "cover")
    
    # Ambil genre
    genre_elements = soup.select("div.komik_info-genre a") or soup.select("td:contains('Genre') + td a")
    genre = ", ".join([g.text.strip() for g in genre_elements]) if genre_elements else "Unknown Genre"
    
    # Ambil tipe
    type_element = soup.select_one("td:contains('Jenis Komik') + td") or soup.select_one("td:contains('Type') + td")
    comic_type = type_element.text.strip() if type_element else "Unknown Type"
    
    # Ambil author
    author_element = soup.select_one("td:contains('Author') + td") or soup.select_one("div.komik_info-author")
    author = author_element.text.strip() if author_element else "Unknown Author"
    
    comic_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    
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
    
    logging.info(f"Komik {title} berhasil ditambahkan dengan ID: {comic_id}")