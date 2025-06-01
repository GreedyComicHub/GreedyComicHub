"""Scrape comic data from Komiku."""
import logging
import requests
import cloudinary
import cloudinary.uploader
import configparser
from typing import Dict, List
from bs4 import BeautifulSoup

# Load config
config = configparser.ConfigParser()
config.read('config.ini')
cloudinary.config(
    cloud_name=config['Cloudinary']['CloudName'],
    api_key=config['Cloudinary']['ApiKey'],
    api_secret=config['Cloudinary']['ApiSecret']
)

def scrape_comic_data(comic_url: str) -> Dict:
    """Scrape comic metadata."""
    logging.info(f"Scraping metadata from {comic_url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(comic_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.select_one("h1.post-title") or soup.select_one("h1.judul")
        title = title.text.strip() if title else ""
        synopsis = soup.select_one("div.sinopsis") or soup.select_one("div[itemprop='description']")
        synopsis = synopsis.text.strip() if synopsis else ""
        cover = soup.select_one("img.cover") or soup.select_one("img[itemprop='image']")
        cover = cover["src"] if cover else ""
        genre = [g.text.strip() for g in soup.select("a.genre, a[itemprop='genre']")]
        comic_type = soup.select_one("span.jenis") or soup.select_one("td:-soup-contains('Type') + td")
        comic_type = comic_type.text.strip() if comic_type else ""

        data = {
            "title": title,
            "synopsis": synopsis,
            "cover": cover,
            "genre": genre,
            "type": comic_type,
            "chapters": {}
        }
        logging.info(f"Scraped metadata for {title}")
        return data
    except Exception as e:
        logging.error(f"Error scraping metadata from {comic_url}: {str(e)}")
        raise

def scrape_chapter_images(chapter_url: str) -> List[str]:
    """Scrape images from a chapter."""
    logging.info(f"Scraping images from {chapter_url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(chapter_url, headers=headers, timeout=10)
        if response.status_code != 200:
            logging.error(f"Failed to access {chapter_url}, status code: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Debug: Simpan HTML
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(soup.pretty_print())
        logging.info(f"Saved HTML to debug.html for {chapter_url}")

        # Selector utama
        images = []
        selectors = [
            "div.konten img[itemprop='image']",
            "div.baca-komik img[itemprop='image']",
            "div.konten img"
        ]
        for selector in selectors:
            img_elements = soup.select(selector)
            logging.info(f"Found {len(img_elements)} <img> elements with selector {selector}")
            
            for img in img_elements:
                src = img.get("src") or img.get("data-src")
                if src and "img.komiku.org/wp-content" in src and "thumbnail" not in src and "lazy.jpg" not in src and "asset" not in src:
                    logging.info(f"Found image source: {src}")
                    try:
                        upload_result = cloudinary.uploader.upload(
                            src,
                            folder=f"greedycomichub/black-clover-indonesia-chapter-01",
                            public_id=src.split("/")[-1].split(".")[0]
                        )
                        images.append(upload_result["secure_url"])
                        logging.info(f"Uploaded image {src} to Cloudinary")
                    except Exception as e:
                        logging.error(f"Failed to upload image {src} to Cloudinary: {str(e)}")
                        continue
            
            if images:
                break
        
        if not images:
            logging.warning(f"No images found at {chapter_url} with main selectors")
            img_elements = soup.select("img[src*='img.komiku.org/wp-content'], img[data-src*='img.komiku.org/wp-content']")
            logging.info(f"Trying fallback selector img[src*='img.komiku.org/wp-content'], found {len(img_elements)} <img> elements")
            for img in img_elements:
                src = img.get("src") or img.get("data-src")
                if src and "thumbnail" not in src and "lazy.jpg" not in src and "asset" not in src:
                    logging.info(f"Found fallback image source: {src}")
                    try:
                        upload_result = cloudinary.uploader.upload(
                            src,
                            folder=f"greedycomichub/black-clover-indonesia-chapter-01",
                            public_id=src.split("/")[-1].split(".")[0]
                        )
                        images.append(upload_result["secure_url"])
                        logging.info(f"Uploaded image {src} to Cloudinary (fallback)")
                    except Exception as e:
                        logging.error(f"Failed to upload image {src} to Cloudinary: {str(e)}")
                        continue
        
        if not images:
            logging.warning(f"No images found at {chapter_url} with any selector")
        else:
            logging.info(f"Found and uploaded {len(images)} images for {chapter_url}")
        return images
    except Exception as e:
        logging.error(f"Error scraping images from {chapter_url}: {str(e)}")
        return []