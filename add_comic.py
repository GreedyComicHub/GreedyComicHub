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
    
    title_element = soup.select_one("h1[itemprop='name']")
    title = title_element.text.strip() if title_element else "Unknown Title"
    
    synopsis_element = soup.select_one("div[itemprop='description']")
    synopsis = synopsis_element.text.strip() if synopsis_element else "No synopsis available."
    synopsis = paraphrase_synopsis(synopsis)
    
    cover_element = soup.select_one("img[itemprop='image']")
    cover_url = cover_element["src"] if cover_element else ""
    if cover_url:
        comic_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        cover_url = upload_to_cloudinary(cover_url, comic_id, "cover")
    
    genre_element = soup.select_one("td:contains('Genre') + td")
    genre = genre_element.text.strip() if genre_element else "Unknown Genre"
    
    type_element = soup.select_one("td:contains('Type') + td")
    comic_type = type_element.text.strip() if type_element else "Unknown Type"
    
    author_element = soup.select_one("td:contains('Author') + td")
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