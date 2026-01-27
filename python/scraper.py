import logging
import re
import requests
from typing import Tuple, Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .utils import fetch_page, paraphrase_synopsis

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://komiku.org/"
}

def get_comic_id_and_display_name(url: str) -> Tuple[str, str]:
    """Extract comic ID and display name from URL.
    
    Args:
        url: Comic URL path.
        
    Returns:
        Tuple of (comic_id, display_name).
    """
    comic_id = path.split("/")[-2] if path.endswith("/") else path.split("/")[-1]
    comic_id = comic_id.replace("manga-", "").replace("/", "")
    display_name = " ".join(word.capitalize() for word in comic_id.split("-"))
    logging.info(f"Nama komik dari URL: ID={comic_id}, Display={display_name}")
    return comic_id, display_name

def scrape_komiku_details(url: str, soup: BeautifulSoup) -> Tuple[str, str, str, str, BeautifulSoup, str, str]:
    """Scrape comic metadata from page.
    
    Args:
        url: Comic page URL.
        soup: BeautifulSoup parsed HTML.
        
    Returns:
        Tuple of (title, author, synopsis, cover_url, soup, genre, comic_type).
    """
    title = title_element.text.strip().replace("Komik ", "").strip() if title_element else "Unknown Title"
    logging.info(f"Nama komik dari <h1>: {title}")
    author = "Unknown Author"
    selectors = [
        (soup.find, "table", {"class": "inftable"}, lambda x: x.find("td", string=lambda t: "Pengarang" in t if t else False)),
        (soup.find, "span", {"string": lambda x: "Author" in x if x else False}, lambda x: x.find_next("span")),
        (soup.find, "td", {"string": lambda x: "Author" in x if x else False}, lambda x: x.find_next("td")),
        (soup.find, "div", {"class": "komik_info-content-meta"}, lambda x: x.find("span", string=lambda t: "Author" in t if t else False)),
        (soup.find_all, "span", {}, lambda x: x if "Author" in x.text else None)
    ]
    for find_method, tag, attrs, next_step in selectors:
        element = find_method(tag, **attrs) if attrs else find_method(tag)
        if element:
            if isinstance(element, list):
                for span in element:
                    next_text = span.find_next_sibling(text=True)
                    if next_text and next_text.strip():
                        author = next_text.strip()
                        break
            else:
                next_element = next_step(element)
                if next_element:
                    if tag == "table":
                        author = next_element.find_next("td").text.strip() if next_element.find_next("td") else "Unknown Author"
                    else:
                        author = next_element.text.strip()
                    if author and author != "Unknown Author":
                        break
                elif element.find_next_sibling(text=True):
                    author = element.find_next_sibling(text=True).strip()
                    if author and author != "Unknown Author":
                        break
    author = author.replace("~", "").strip() if author else "Unknown Author"
    logging.info(f"Author ditemukan: {author}")
    genre = "Fantasy"
    genre_selectors = [
        (soup.find, "table", {"class": "inftable"}, lambda x: x.find("td", string=lambda t: "Konsep Cerita" in t if t else False)),
        (soup.find, "span", {"string": lambda x: "Genre" in x if x else False}, lambda x: x.find_next("span")),
        (soup.find, "td", {"string": lambda x: "Genre" in x if x else False}, lambda x: x.find_next("td")),
        (soup.find, "div", {"class": "komik_info-content-genre"}, lambda x: x)
    ]
    for find_method, tag, attrs, next_step in genre_selectors:
        element = find_method(tag, **attrs)
        if element:
            next_element = next_step(element)
            if next_element:
                if tag == "table":
                    genre = next_element.find_next("td").text.strip() if next_element.find_next("td") else "Fantasy"
                else:
                    genre = next_element.text.strip()
                if genre:
                    break
    logging.info(f"Genre ditemukan: {genre}")
    comic_type = "Unknown Type"
    type_selectors = [
        (soup.find, "table", {"class": "inftable"}, lambda x: x.find("td", string=lambda t: t and "Jenis Komik" in t)),
        (soup.find, "span", {"string": lambda x: x and "Type" in x}, lambda x: x.find_next("span")),
        (soup.find, "td", {"string": lambda x: x and "Type" in x}, lambda x: x.find_next("td")),
        (soup.find, "div", {"class": "komik_info-content-meta"}, lambda x: x.find("span", string=lambda t: t and "Type" in t)),
        (soup.find, "span", {"class": "komik_info-content-type"}, lambda x: x)
    ]
    for find_method, tag, attrs, next_step in type_selectors:
        element = find_method(tag, **attrs)
        if element:
            next_element = next_step(element) if next_step else element
            if next_element:
                if tag == "table":
                    comic_type = next_element.find_next("td").text.strip() if next_element.find_next("td") else "Unknown Type"
                else:
                    comic_type = next_element.text.strip()
                if comic_type and comic_type != "Unknown Type":
                    break
            elif element.text.strip():
                comic_type = element.text.strip()
                if comic_type:
                    break
    logging.info(f"Tipe komik ditemukan: {comic_type}")
    synopsis = "No synopsis available."
    synopsis_header = soup.find("h2", string=lambda t: t and "Sinopsis Lengkap" in t)
    if synopsis_header:
        synopsis_element = synopsis_header.find_next("p")
        if synopsis_element:
            synopsis = synopsis_element.text.strip()
            logging.info(f"Sinopsis ditemukan dari <p> setelah <h2>Sinopsis Lengkap</h2>: {synopsis[:100]}...")
    if synopsis == "No synopsis available.":
        logging.warning("Sinopsis tidak ditemukan di <p> setelah <h2>. Mencoba fallback ke div.desc.")
        synopsis_element = soup.find("div", class_="desc")
        if synopsis_element:
            synopsis = synopsis_element.text.strip()
        else:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                synopsis = meta_desc["content"].strip()
    synopsis = paraphrase_synopsis(synopsis)
    cover_url = ""
    cover_selectors = [
        'meta[property="og:image"]',
        'meta[itemprop="image"]',
        'img[itemprop="image"]',
        'img.komik_info-cover-image'
    ]
    for selector in cover_selectors:
        cover_element = soup.select_one(selector)
        if cover_element:
            cover_url = cover_element.get("content") or cover_element.get("src") or ""
            if cover_url and cover_url.startswith('http'):
                break
    if not cover_url:
        logging.warning("Cover image tidak ditemukan dengan selector utama. Mencoba fallback.")
        cover_image = soup.find("img", class_=lambda x: x and "cover" in x.lower())
        if cover_image:
            cover_url = cover_image.get("src", "")
    if not cover_url:
        logging.error("Cover image tidak ditemukan.")
    logging.info(f"Scraped data: title={title}, author={author}, genre={genre}, type={comic_type}, synopsis={synopsis}, cover={cover_url}")
    return title, author, synopsis, cover_url, soup, genre, comic_type

def scrape_comic_details(url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[BeautifulSoup], Optional[str], Optional[str]]:
    """Fetch and scrape comic details from URL.
    
    Args:
        url: Comic page URL.
        
    Returns:
        Tuple of (title, author, synopsis, cover_url, soup, genre, comic_type) or Nones on error.
    """
    if not html:
        return None, None, None, None, None, None, None
    soup = BeautifulSoup(html, "html.parser")
    return scrape_komiku_details(url, soup)

def scrape_chapter_list(url: str, soup: BeautifulSoup) -> Dict[str, str]:
    """Extract chapter list from page.
    
    Args:
        url: Comic page URL.
        soup: BeautifulSoup parsed HTML.
        
    Returns:
        Dictionary of {chapter_num: chapter_url}.
    """
    logging.info(f"Mencari daftar chapter dari {url}...")
    # Selector utama dan fallback
    selectors = [
        'td.judulseries a',
        'table tr a:has(span)',
        'a[href*="-chapter-"]',
        'div.bxcl ul li a'
    ]
    for selector in selectors:
        chapter_elements = soup.select(selector)
        if chapter_elements:
            logging.info(f"Chapter ditemukan dengan selector: {selector}")
            for element in chapter_elements:
                href = element.get("href", "").strip()
                if not href or "chapter" not in href.lower():
                    continue
                if href.startswith('/'):
                    href = urljoin(url, href)
                chapter_text = element.find('span').text.strip() if element.find('span') else element.text.strip()
                # Regex untuk tangkap integer atau desimal (misal 1, 1.1, 302.5)
                match = re.search(r'Chapter\s+(\d+(\.\d+)?)', chapter_text, re.IGNORECASE)
                if match:
                    chapter_num = float(match.group(1))
                    chapter_num = int(chapter_num) if chapter_num.is_integer() else chapter_num
                    chapters[str(chapter_num)] = href
                    logging.debug(f"Chapter {chapter_num}: {href}")
            if chapters:
                break
    if not chapters:
        logging.warning(f"Tidak ditemukan chapter di {url}. HTML mungkin berubah.")
    return chapters

def scrape_chapter_images(chapter_url: str) -> List[str]:
    """Extract image URLs from chapter.
    
    Args:
        chapter_url: Chapter page URL.
        
    Returns:
        List of image URLs.
    """
    full_url = urljoin("https://komiku.org", chapter_url)
    html = fetch_page(full_url, retries=3, delay=2)
    if not html:
        logging.error(f"Failed to fetch chapter: {chapter_url}")
        return []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        title_element = soup.find("h1")
        chapter_title = title_element.text.strip() if title_element else "Unknown Chapter"
        logging.info(f"Judul chapter: {chapter_title}")
        
        image_urls = []
        selectors = [
            'img[itemprop="image"]',
            '#readerarea img',
            'div.komik img',
            'img[src*="img.komiku.org"]'
        ]
        for selector in selectors:
            image_elements = soup.select(selector)
            if image_elements:
                for img in image_elements:
                    src = img.get("src", "")
                    if src and src.startswith("http"):
                        image_urls.append(src)
                break
        if not image_urls:
            logging.error(f"Tidak ada gambar untuk chapter ini: {chapter_url}")
        else:
            logging.info(f"Extracted {len(image_urls)} images from {chapter_title}")
        return image_urls
    except Exception as e:
        logging.error(f"Error parsing chapter images from {chapter_url}: {e}")
        return []