"""Scrape comic data from Komiku."""
import logging
import requests
import cloudinary.uploader
from typing import Dict, List
from bs4 import BeautifulSoup

def scrape_comic_data(comic_url: str) -> Dict:
    """Scrape comic metadata."""
    logging.info(f"Scraping metadata from {comic_url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(comic_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.select_one("h1[itemprop='name']").text.strip() if soup.select_one("h1[itemprop='name']") else ""
        synopsis = soup.select_one("div[itemprop='description']").text.strip() if soup.select_one("div[itemprop='description']") else ""
        cover = soup.select_one("img[itemprop='image']")["src"] if soup.select_one("img[itemprop='image']") else ""
        genre = [g.text.strip() for g in soup.select("a[itemprop='genre']")]
        comic_type = soup.select_one("td:contains('Type') + td").text.strip() if soup.select_one("td:contains('Type') + td") else ""

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
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        images = []
        for img in soup.select("#article img"):
            src = img.get("src")
            if src:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    src,
                    folder=f"greedycomichub/{chapter_url.split('/')[-2]}/{chapter_url.split('/')[-1]}",
                    public_id=src.split("/")[-1].split(".")[0]
                )
                images.append(upload_result["secure_url"])
        if not images:
            logging.warning(f"No images found at {chapter_url}")
        else:
            logging.info(f"Found and uploaded {len(images)} images for {chapter_url}")
        return images
    except Exception as e:
        logging.error(f"Error scraping images from {chapter_url}: {str(e)}")
        return []