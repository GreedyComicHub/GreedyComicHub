"""Scraper for Komiku comic data."""
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import re
import logging
import time
from utils import get_comic_id_from_url

def setup_driver() -> webdriver.Chrome:
    """Set up headless Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service("chromedriver.exe")
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_comic_data(comic_url: str) -> dict:
    """Scrape comic data from Komiku."""
    logging.info(f"Scraping data from {comic_url}")
    try:
        driver = setup_driver()
        driver.get(comic_url)
        time.sleep(2)  # Tunggu halaman load
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        # Judul dari <h1 class="judul">
        title_elem = soup.find("h1", class_="judul")
        title = title_elem.text.strip().replace("Komik ", "") if title_elem else "Unknown Title"

        # Default value
        author = "Unknown Author"
        genre = "Unknown Genre"
        comic_type = "Unknown Type"
        synopsis = "No synopsis available."
        cover = ""

        # Cari author, genre, type dari <table class="data">
        table = soup.find("table", class_="data")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) == 2:
                    key = cells[0].text.strip().lower()
                    value = cells[1].text.strip()
                    if key == "pengarang":
                        author = value
                    elif key == "genre":
                        genre = value
                    elif key == "tipe":
                        comic_type = value

        # Sinopsis dari <div class="sin"><p>
        synopsis_elem = soup.find("div", class_="sin")
        if synopsis_elem:
            p = synopsis_elem.find("p")
            if p:
                synopsis = p.text.strip()
                synopsis = re.sub(r"Baca Komik.*di Komiku\.", "", synopsis).strip()
                synopsis = synopsis.lower().replace(title.lower(), title)

        # Cover dari <div class="ims"><img>
        cover_elem = soup.find("div", class_="ims")
        if cover_elem:
            img = cover_elem.find("img")
            if img and img.get("src"):
                cover = img["src"]

        data = {
            "title": title,
            "author": author,
            "synopsis": synopsis,
            "cover": cover,
            "genre": genre,
            "type": comic_type,
            "chapters": {}
        }
        logging.info(f"Scraped data: {data}")
        return data
    except Exception as e:
        logging.error(f"Error scraping {comic_url}: {str(e)}")
        raise

def scrape_chapter_images(chapter_url: str) -> list:
    """Scrape chapter images from Komiku."""
    logging.info(f"Scraping images from {chapter_url}")
    try:
        driver = setup_driver()
        driver.get(chapter_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        images = []
        img_elements = soup.find_all("img", class_="isi-konten")
        for img in img_elements:
            if img.get("src"):
                images.append(img["src"])
        return images
    except Exception as e:
        logging.error(f"Error scraping images from {chapter_url}: {str(e)}")
        raise