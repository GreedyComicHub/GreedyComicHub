import logging
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from utils import fetch_page, paraphrase_synopsis

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://komiku.org/"
}

def get_comic_id_and_display_name(url):
    path = urlparse(url).path
    comic_id = path.split("/")[-2] if path.endswith("/") else path.split("/")[-1]
    comic_id = comic_id.replace("manga-", "").replace("/", "")
    display_name = " ".join(word.capitalize() for word in comic_id.split("-"))
    logging.info(f"Nama komik dari URL: ID={comic_id}, Display={display_name}")
    return comic_id, display_name

def scrape_komiku_details(url, soup):
    title_element = soup.find("h1")
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

    comic_type = "Manhua"
    type_selectors = [
        (soup.find, "table", {"class": "inftable"}, lambda x: x.find("td", string=lambda t: "Jenis Komik" in t if t else False)),
        (soup.find, "span", {"string": lambda x: "Type" in x if x else False}, lambda x: x.find_next("span")),
        (soup.find, "td", {"string": lambda x: "Type" in x if x else False}, lambda x: x.find_next("td")),
        (soup.find, "div", {"class": "komik_info-content-meta"}, lambda x: x.find("span", string=lambda t: "Type" in t if t else False))
    ]
    for find_method, tag, attrs, next_step in type_selectors:
        element = find_method(tag, **attrs)
        if element:
            next_element = next_step(element)
            if next_element:
                if tag == "table":
                    comic_type = next_element.find_next("td").text.strip() if next_element.find_next("td") else "Manhua"
                else:
                    comic_type = next_element.text.strip()
                if comic_type:
                    break
            elif element.find_next_sibling(text=True):
                comic_type = element.find_next_sibling(text=True).strip()
                if comic_type:
                    break
    logging.info(f"Tipe komik ditemukan: {comic_type}")

    synopsis = "No synopsis available."
    synopsis_header = soup.find("h2", string=lambda t: "Sinopsis Lengkap" in t if t else False)
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
        'img[itemprop="image"]'
    ]
    for selector in cover_selectors:
        cover_element = soup.select_one(selector)
        if cover_element and cover_element.get("content"):
            cover_url = cover_element["content"]
            break
        elif cover_element and cover_element.get("src"):
            cover_url = cover_element["src"]
            break
    if not cover_url:
        logging.warning("Cover image tidak ditemukan.")
    logging.info(f"Scraped data: title={title}, author={author}, genre={genre}, type={comic_type}, synopsis={synopsis}, cover={cover_url}")
    return title, author, synopsis, cover_url, soup, genre, comic_type

def scrape_comic_details(url):
    html = fetch_page(url)
    if not html:
        return None, None, None, None, None, None, None
    soup = BeautifulSoup(html, "html.parser")
    return scrape_komiku_details(url, soup)

def scrape_chapter_list(url, soup):
    chapters = {}
    logging.info(f"Mencari daftar chapter dari {url}...")
    chapter_elements = soup.select("td.judulseries a")
    if not chapter_elements:
        logging.warning("Tidak ditemukan chapter. Mencoba fallback...")
        all_links = soup.select("a[href*='chapter']")
        for link in all_links:
            href = link.get("href", "")
            if "chapter" in href.lower():
                chapter_text = link.text.strip()
                match = re.search(r'Chapter\s+(\d+(\.\d+)?)', chapter_text, re.IGNORECASE)
                if match:
                    chapter_num = match.group(1)
                    chapters[chapter_num] = href
                    # logging.info(f"Chapter {chapter_num} ditemukan via fallback: {href}")
    for element in chapter_elements:
        href = element.get("href", "")
        chapter_text = element.text.strip()
        match = re.search(r'Chapter\s+(\d+(\.\d+)?)', chapter_text, re.IGNORECASE)
        if match:
            chapter_num = match.group(1)
            chapters[chapter_num] = href
            # logging.info(f"Chapter {chapter_num}: {href}")
    return chapters

def scrape_chapter_images(chapter_url):
    full_url = urljoin("https://komiku.org", chapter_url)
    html = fetch_page(full_url)
    if not html:
        return []
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
    return image_urls