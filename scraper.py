"""Scraper for Komiku comic data."""
import logging
from typing import Dict, List, Optional
import re
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from utils import get_comic_id_from_url

def setup_driver() -> Optional[WebDriver]:
    """Set up headless Chrome driver with custom user-agent.

    Returns:
        WebDriver: Initialized Chrome driver or None if failed.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    service = Service("chromedriver.exe")
    try:
        driver = WebDriver(service=service, options=chrome_options)
        logging.info("Chrome driver initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error initializing Chrome driver: {e}")
        return None

def scrape_comic_data(comic_url: str) -> Dict[str, str]:
    """Scrape comic data from Komiku with fallback to requests.

    Args:
        comic_url (str): URL of the comic page.

    Returns:
        Dict[str, str]: Scraped comic data.

    Raises:
        Exception: If scraping fails.
    """
    logging.info(f"Scraping data from {comic_url}")
    soup = None
    try:
        # Try Selenium first
        driver = setup_driver()
        if driver:
            try:
                driver.get(comic_url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "judul"))
                )
                soup = BeautifulSoup(driver.page_source, "html.parser")
                logging.info("Page source retrieved via Selenium.")
            except Exception as e:
                logging.warning(f"Selenium failed: {e}")
            finally:
                driver.quit()

        # Fallback to requests
        if not soup:
            logging.info("Falling back to requests.")
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(comic_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            logging.info("Page source retrieved via requests.")

        # Debug: Save HTML
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        logging.info("Saved page source to debug.html.")

        # Extract title
        title_elem = soup.find("h1", class_="judul")
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
        table = soup.find("table", class_="data")
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
                    elif key == "genre":
                        data["genre"] = value
                    elif key == "tipe":
                        data["type"] = value
        else:
            logging.warning("Data table not found.")

        # Extract synopsis
        synopsis_elem = soup.find("div", class_="sin")
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
        cover_elem = soup.find("div", class_="ims")
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
        logging.error(f"Error scraping {comic_url}: {e}")
        raise

def scrape_chapter_images(chapter_url: str) -> List[str]:
    """Scrape chapter images from Komiku.

    Args:
        chapter_url (str): URL of the chapter page.

    Returns:
        List[str]: List of image URLs.

    Raises:
        Exception: If scraping fails.
    """
    logging.info(f"Scraping images from {chapter_url}")
    try:
        driver = setup_driver()
        if driver:
            driver.get(chapter_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "isi-konten"))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()
        else:
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
        logging.error(f"Error scraping images from {chapter_url}: {e}")
        raise