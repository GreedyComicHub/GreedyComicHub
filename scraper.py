"""Scraper for Komiku comic data."""
import logging
import re
import requests
from typing import Dict, List
from bs4 import BeautifulSoup
from utils import get_comic_id_from_url

def scrape_comic_data(comic_url: str) -> Dict[str, any]:
    """Scrape comic data from Komiku using requests."""
    logging.info(f"Scraping data from {comic_url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
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
                    elif key in ("genre", "kategori"):
                        genres = [a.text.strip() for a in cells[1].find_all("a")]
                        data["genre"] = ", ".join(genres) if genres else value
                    elif key in ("tipe", "tipe komik", "jenis komik"):
                        data["type"] = value
        else:
            logging.warning("Data table not found.")

        # Extract synopsis
        synopsis_elem = (
            soup.find("div", class_="sinopsis")
            or soup.find("div", class_="sin")
            or soup.find("div", class_="desc")
        )
        if synopsis_elem:
            p = synopsis_elem.find("p")
            if p:
                synopsis = p.text.strip()
                synopsis = re.sub(r"Baca Komik.*di Komiku\.", "", synopsis).strip()
                synopsis = synopsis.lower().replace(title.lower(), title)
                data["synopsis"] = synopsis
                logging.info(f"Synopsis found: {synopsis}")
        else:
            logging.warning("Synopsis div not found.")

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
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
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