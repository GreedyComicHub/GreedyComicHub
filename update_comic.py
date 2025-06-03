import logging
import os
import configparser
import cloudinary
import cloudinary.uploader
from scraper import scrape_chapter_list, scrape_chapter_images, get_comic_id_and_display_name
from utils import read_json, write_json, fetch_page, DATA_DIR
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Setup Cloudinary from config.ini
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
cloudinary.config(
    cloud_name=config["Cloudinary"]["CloudName"],
    api_key=config["Cloudinary"]["ApiKey"],
    api_secret=config["Cloudinary"]["ApiSecret"]
)

def update_comic(url, start, end, overwrite=False):
    """Update komik dengan chapter dari start sampai end, upload gambar ke Cloudinary."""
    logging.info(f"Mulai update chapter: {url}")
    comic_id, display_name = get_comic_id_and_display_name(url)
    logging.info(f"Nama komik dari URL: ID={comic_id}, Display={display_name}")

    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if not os.path.exists(comic_file):
        logging.error(f"File {comic_file} nggak ada. Jalankan 'add-comic' dulu.")
        return

    comic_data = read_json(comic_file)
    chapters = comic_data.get("chapters", {})

    html = fetch_page(url)
    if not html:
        logging.error(f"Gagal mengambil halaman {url}.")
        return
    soup = BeautifulSoup(html, "html.parser")
    chapter_list = scrape_chapter_list(url, soup)
    if not chapter_list:
        logging.error(f"Nggak ada chapter ditemukan untuk {comic_id}.")
        return

    updated = False
    for chapter_num in sorted(chapter_list.keys(), key=float):
        if float(chapter_num) < start or float(chapter_num) > end:
            continue
        if chapter_num in chapters and not overwrite:
            logging.info(f"Chapter {chapter_num} untuk {comic_id} udah ada, skip.")
            continue

        chapter_url = urljoin(url, chapter_list[chapter_num])
        logging.info(f"Mencoba nambah chapter {chapter_num} dari {chapter_url}")
        image_urls = scrape_chapter_images(chapter_url)
        if not image_urls:
            logging.error(f"Gagal scrape gambar untuk chapter {chapter_num}.")
            continue

        # Upload ke Cloudinary
        cloudinary_urls = []
        for img_url in image_urls:
            try:
                uploaded = cloudinary.uploader.upload(
                    img_url,
                    folder=f"comics/{comic_id}/{chapter_num}",
                    resource_type="image"
                )
                cloudinary_urls.append(uploaded["secure_url"])
            except Exception as e:
                logging.error(f"Gagal upload gambar {img_url} ke Cloudinary: {e}")
                continue

        if not cloudinary_urls:
            logging.error(f"Tidak ada gambar berhasil diupload untuk chapter {chapter_num}.")
            continue

        chapters[chapter_num] = {
            "images": cloudinary_urls,
            "title": f"Chapter {chapter_num}"
        }
        logging.info(f"Berhasil nambah chapter {chapter_num} dengan {len(cloudinary_urls)} gambar.")
        updated = True

    if updated:
        comic_data["chapters"] = chapters
        write_json(comic_file, comic_data)
        logging.info(f"Berhasil disimpan ke {comic_file}")