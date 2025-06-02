import logging
from utils import fetch_page, paraphrase_synopsis
from bs4 import BeautifulSoup

def scrape_chapter_list(url, soup):
    try:
        chapters = {}
        chapter_elements = soup.select(".chapter-link")
        for elem in chapter_elements:
            chapter_num = elem.text.strip().replace("Chapter ", "")
            chapter_url = elem["href"]
            chapters[chapter_num] = {"url": chapter_url, "date": "Unknown"}
        return chapters
    except Exception as e:
        logging.error(f"Gagal scrape chapter list: {e}")
        return {}

def scrape_chapter_images(chapter_url):
    try:
        html = fetch_page(chapter_url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        images = [img["src"] for img in soup.select(".chapter-image img")]
        return images
    except Exception as e:
        logging.error(f"Gagal scrape images: {e}")
        return []

def get_comic_id_and_display_name(url):
    try:
        comic_id = url.split("/")[-1] or url.split("/")[-2]
        html = fetch_page(url)
        soup = BeautifulSoup(html, "html.parser")
        display_name = soup.select_one("h1").text.strip() if soup.select_one("h1") else comic_id
        return comic_id, display_name
    except Exception as e:
        logging.error(f"Gagal get comic info: {e}")
        return None, None