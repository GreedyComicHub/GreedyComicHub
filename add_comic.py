import logging
import os
<<<<<<< HEAD
from scraper import scrape_comic_details, get_comic_id_and_display_name
from utils import read_json, write_json, upload_to_cloudinary, DATA_DIR

def add_comic(url):
    logging.info(f"Menambahkan komik baru: {url}")
    comic_id, _ = get_comic_id_and_display_name(url)
    title, author, synopsis, cover_url, soup, genre, comic_type = scrape_comic_details(url)
    if not title:
        logging.error("Gagal mendapatkan detail komik.")
        return
    cover_cloudinary_url = cover_url
    if cover_url:
        try:
            cover_cloudinary_url = upload_to_cloudinary(cover_url, comic_id, "cover")
            logging.info(f"Cover diupload ke Cloudinary: {cover_cloudinary_url}")
        except Exception as e:
            logging.error(f"Gagal upload cover ke Cloudinary: {e}")
            logging.info(f"Fallback ke URL asli untuk cover: {cover_cloudinary_url}")
    comic_data = {
        "title": title,
        "author": author,
        "synopsis": synopsis,
        "cover": cover_cloudinary_url,
        "genre": genre,
        "type": comic_type,
        "chapters": {},
        "source_url": url.strip()  # Simpen URL asli, bersihin spasi
    }
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if os.path.exists(comic_file):
        existing_data = read_json(comic_file)
        comic_data["chapters"] = existing_data.get("chapters", {})
        comic_data["source_url"] = existing_data.get("source_url", url.strip())
        logging.info(f"Komik sudah ada, mempertahankan chapters dan source_url.")
    write_json(comic_file, comic_data)
    logging.info(f"Berhasil simpan data komik ke {comic_file}")
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
        "total_chapters": len(comic_data["chapters"]),
        "source_url": comic_data["source_url"]  # Ambil dari comic_data
    }
    write_json(index_file, index_data)
    logging.info(f"Berhasil update indeks di {index_file}")
=======
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
>>>>>>> 4b15c6dc1e741c004a4dedbad5589a76d2074390
