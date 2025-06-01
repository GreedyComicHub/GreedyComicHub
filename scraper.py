"""Scraper for Komiku comic data."""
import logging
import re
import random
import requests
from typing import Dict, List
from bs4 import BeautifulSoup
from utils import get_comic_id_from_url

def paraphrase_synopsis(text: str, title: str) -> str:
    """Paraphrase synopsis text using simple word replacement."""
    try:
        # Simple word replacements
        replacements = {
            "berjuang": "berusaha keras",
            "mimpi": "cita-cita",
            "kerajaan": "negeri",
            "persahabatan": "ikatan sahabat",
            "perjalanan": "petualangan",
            "melindungi": "menjaga",
            "tekad": "semangat",
            "tantangan": "rintangan"
        }
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        # Randomly shuffle sentences
        sentences = [s.strip() for s in result.split(".") if s.strip()]
        if len(sentences) > 1:
            random.shuffle(sentences)
            result = ". ".join(sentences) + "."
        
        # Clean and normalize
        result = re.sub(r"Baca Komik.*di Komiku\.", "", result).strip()
        result = result.lower().replace(title.lower(), title)
        return result if result else text
    except Exception as e:
        logging.error(f"Error paraphrasing synopsis: {str(e)}")
        return text

def scrape_comic_data(comic_url: str) -> Dict[str, str]:
    """Scrape comic data from Komiku using requests."""
    logging.info(f"Scraping data from {comic_url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(comic_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        logging.info("Page source retrieved via requests.")

        # Debug HTML
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        logging.info("Saved page source to debug.html.")

        # Extract title
        title_elem = soup.find("h1", class_="judul") or soup.find("h1")
        title = title_elem.text.strip().replace("Komik ", "") if title_elem else "Unknown Title"
        logging.info(f"Title found: {title}")

        # Default values
        data = {
            "title": title,
            "author": "Unknown Author",
            "synopsis": "No synopsis available.",
            "cover": "",
            "genre": "Unknown Genre",
            "type": "Unknown Type",
            "chapters": {}
        }

        # Extract author, genre, type
        table = soup.find("table", class_="data") or soup.find("table")
        if table:
            logging.info("Found data table.")
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) == 2:
                    key = cells[0].text.strip().lower()
                    value = cells[1].text.strip()
                    logging.info(f"Table row: {key} = {value}")
                    if key == "pengarang":
                        data["author"] = value
                    elif key in ("genre", "kategori", "konsep cerita"):
                        genres = [a.text.strip() for a in cells[1].find_all("a")]
                        data["genre"] = ", ".join(genres) if genres else value
                    elif key in ("tipe", "tipe komik", "jenis komik"):
                        data["type"] = value
        else:
            logging.warning("Data table not found.")

        # Extract synopsis
        synopsis_elem = None
        for h2 in soup.find_all("h2"):
            if h2.text.strip().lower() == "sinopsis lengkap":
                synopsis_elem = h2.find_next("p")
                break
        if synopsis_elem:
            synopsis = synopsis_elem.text.strip()
            synopsis = re.sub(r"Baca Komik.*di Komiku\.", "", synopsis).strip()
            if synopsis:
                paraphrased = paraphrase_synopsis(synopsis, title)
                data["synopsis"] = paraphrased
                logging.info(f"Synopsis found: {paraphrased}")
        else:
            logging.warning("Synopsis paragraph not found.")

        # Extract cover
        cover_elem = soup.find("div", class_="ims") or soup.find("div", class_="cover")
        if cover_elem:
            img = cover_elem.find("img")
            if img:
                cover = img.get("data-src") or img.get("src")
                if cover:
                    data["cover"] = cover
                    logging.info(f"Cover found: {cover}")
        else:
            logging.warning("Cover div not found.")

        logging.info(f"Scraped data: {data}")
        return data
    except Exception as e:
        logging.error(f"Error scraping {comic_url}: {str(e)}")
        raise

def scrape_chapter_images(chapter_url: str) -> List[str]:
    """Scrape chapter images from Komiku."""
    logging.info(f"Scraping images from {chapter_url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(chapter_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        images = []
        for img in soup.find_all("img", class_="isi-konten"):
            src = img.get("data-src") or img.get("src")
            if src:
                images.append(src)
                logging.info(f"Image found: {src}")
        return images
    except Exception as e:
        logging.error(f"Error scraping images from {chapter_url}: {str(e)}")
        raise