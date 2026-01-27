import logging
import time
import random
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KomikuScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.base_url = "https://komiku.org"

    def _get_headers(self):
        """Get headers with random user agent"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def _human_delay(self):
        """Add human-like delay between requests"""
        time.sleep(random.uniform(2, 5))

    def scrape_manga_list(self, manga_type="manga", limit=None):
        """Scrape list of manga from komiku.org
        
        Args:
            manga_type: Type of manga (manga, manhua, manhwa)
            limit: Maximum number of manga to scrape (None = unlimited)
        """
        manga_list = []
        page = 1
        max_pages = 50
        
        try:
            while page <= max_pages:
                # Stop if limit reached
                if limit and len(manga_list) >= limit:
                    break
                
                url = f"{self.base_url}/daftar-komik/?tipe={manga_type}&page={page}"
                logger.info(f"Scraping page {page}: {url}")
                
                response = self.session.get(url, headers=self._get_headers(), timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Find manga items
                found_on_page = False
                
                # Try multiple selectors
                items = soup.find_all("a", class_=re.compile("komik|manga", re.I))
                
                for item in items:
                    # Stop if limit reached
                    if limit and len(manga_list) >= limit:
                        break
                    
                    href = item.get("href")
                    if not href or "/manga/" not in href:
                        continue
                    
                    # Get title
                    title_elem = item.find(["h3", "h2", "p"])
                    if title_elem:
                        title = title_elem.text.strip()
                    else:
                        title = item.get("title", item.get("alt", "Unknown"))
                    
                    if title and href:
                        slug = href.rstrip("/").split("/")[-1]
                        manga_list.append({
                            "title": title,
                            "url": urljoin(self.base_url, href),
                            "slug": slug
                        })
                        found_on_page = True
                
                if not found_on_page:
                    logger.info(f"No manga found on page {page}. Stopping.")
                    break
                
                self._human_delay()
                page += 1
            
            # Remove duplicates
            seen = set()
            unique_manga = []
            for manga in manga_list:
                if manga["slug"] not in seen:
                    seen.add(manga["slug"])
                    unique_manga.append(manga)
                # Stop if limit reached
                if limit and len(unique_manga) >= limit:
                    unique_manga = unique_manga[:limit]
                    break
            
            logger.info(f"Found {len(unique_manga)} unique manga")
            return unique_manga
            
        except Exception as e:
            logger.error(f"Error scraping manga list: {e}")
            return manga_list

    def scrape_manga_detail(self, url):
        """Scrape manga detail page"""
        try:
            logger.info(f"Scraping detail: {url}")
            
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract title
            title = "Unknown"
            title_elem = soup.find("h1") or soup.find(["h2", "h3"])
            if title_elem:
                title = title_elem.text.strip()
            
            # Extract author, genre, type - find in table rows
            author = "Unknown"
            genre = ""
            manga_type = "Manga"
            
            # Find info section
            for tr in soup.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    label = tds[0].text.strip().lower()
                    value = tds[1]
                    
                    if "penulis" in label or "author" in label or "pengarang" in label:
                        author = value.text.strip()
                    elif "genre" in label:
                        genre_links = value.find_all("a")
                        genre = ", ".join([link.text.strip() for link in genre_links])
                    elif "tipe" in label or "type" in label:
                        manga_type = value.text.strip()
            
            # Extract cover image - look for image with specific class patterns
            cover = ""
            for img in soup.find_all("img"):
                src = img.get("data-src") or img.get("src") or ""
                alt = img.get("alt", "").lower()
                if src and ("thumbnail" in src or "cover" in alt or "manga" in alt):
                    cover = src
                    break
            
            cover = urljoin(self.base_url, cover) if cover and not cover.startswith("http") else cover
            
            # Extract synopsis - look specifically in main content area
            synopsis = ""
            
            # First try: look for div with specific class patterns
            for div in soup.find_all("div"):
                classes = " ".join(div.get("class", []))
                if "sinopsis" in classes.lower() or "descript" in classes.lower() or "konten" in classes.lower():
                    text = div.text.strip()
                    if len(text) > 100:
                        synopsis = text
                        break
            
            # Second try: find text after synopsis label
            if not synopsis:
                text_found = False
                for elem in soup.find_all(["p", "div", "span"]):
                    if "sinopsis" in elem.text.lower() and not text_found:
                        text_found = True
                        continue
                    if text_found:
                        text = elem.text.strip()
                        if len(text) > 50 and "login" not in text.lower():
                            synopsis = text
                            break
            
            # Fallback: find longest text paragraph that doesn't look like UI
            if not synopsis:
                candidates = []
                for elem in soup.find_all(["p", "div"]):
                    text = elem.text.strip()
                    if len(text) > 100 and "login" not in text.lower() and "google" not in text.lower():
                        candidates.append(text)
                if candidates:
                    # Sort by length and take the longest
                    candidates.sort(key=len, reverse=True)
                    synopsis = candidates[0]
            
            # Get chapter links
            chapter_links = {}
            
            # Find all links that look like chapters
            for link in soup.find_all("a"):
                href = link.get("href", "")
                text = link.text.strip()
                
                if href and ("/chapter-" in href or "-chapter-" in href.lower() or re.search(r"ch[ap].*\d+", text, re.I)):
                    full_url = urljoin(self.base_url, href)
                    # Avoid duplicates
                    if full_url not in chapter_links.values():
                        chapter_links[text] = full_url
            
            return {
                "title": title,
                "author": author,
                "genre": genre,
                "type": manga_type,
                "cover": cover,
                "synopsis": synopsis if synopsis else "No synopsis available",
                "chapter_links": chapter_links,
                "total_chapters": len(chapter_links)
            }
            
        except Exception as e:
            logger.error(f"Error scraping detail: {e}")
            return {
                "title": "Unknown",
                "author": "Unknown",
                "genre": "",
                "type": "Manga",
                "cover": "",
                "synopsis": "Failed to load synopsis",
                "chapter_links": {},
                "total_chapters": 0
            }

    def scrape_chapter_images(self, chapter_url):
        """Scrape image URLs from chapter page"""
        images = []
        
        try:
            logger.info(f"Scraping chapter: {chapter_url}")
            
            response = self.session.get(chapter_url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find Baca_Komik div
            baca_komik = soup.find("div", id="Baca_Komik")
            
            if baca_komik:
                img_tags = baca_komik.find_all("img")
                for img in img_tags:
                    img_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                    
                    if img_url:
                        # Make full URL if relative
                        if not img_url.startswith("http"):
                            img_url = urljoin(self.base_url, img_url)
                        
                        # Skip placeholder or tracking pixels
                        if not any(skip in img_url.lower() for skip in ["1x1", "placeholder", "ads", "banner"]):
                            images.append(img_url)
            
            logger.info(f"Found {len(images)} image URLs in chapter")
            return images
            
        except Exception as e:
            logger.warning(f"Error loading chapter: {e}")
            return []

    def paraphrase_synopsis(self, text):
        """Paraphrase synopsis to casual Indonesian (gaul) style"""
        if not text or len(text) < 10:
            return text
        
        # Remove multiple spaces and clean up
        text = " ".join(text.split())
        
        # Dictionary of replacements to make text more casual
        replacements = {
            r"\bmengikuti kisah\b": "mengikutin cerita",
            r"\bcerita tentang\b": "cerita yang menceritain",
            r"\bberjuang\b": "berusaha keras",
            r"\bmenghadapi\b": "ngedepain",
            r"\bberusaha untuk\b": "nyoba untuk",
            r"\bberusaha\b": "nyoba",
            r"\bmemahami\b": "ngerti",
            r"\bmengerti\b": "ngerti",
            r"\bmencari\b": "nyari",
            r"\bberubah\b": "berubah total",
            r"\bsisi gelap\b": "hal-hal kelam",
            r"\bmemengaruhi\b": "ngasih pengaruh ke",
            r"\bhubungan\b": "hubungan sama",
            r"\bperjalanan\b": "petualangan seru",
            r"\bkarakter\b": "tokoh",
            r"\bkonflik\b": "pertarungan",
            r"\bperilaku\b": "tingkah laku",
            r"\bakar\b": "asal-usul",
            r"\bkebaikan\b": "kebaikan hati",
            r"\bkomik\b": "manga",
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Add casual markers to some sentences
        result = []
        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if sent:
                # Remove trailing punctuation for manipulation
                punct = ""
                if sent and sent[-1] in ".!?":
                    punct = sent[-1]
                    sent = sent[:-1]
                
                # Add casual marker to some sentences
                if i > 0 and random.random() > 0.6:  # Add to ~40% of sentences
                    casual_ends = [" gitu, bro!", " deh!", " lah!", ", gitu aja.", " sih.", " nih!"]
                    sent = sent + random.choice(casual_ends)
                else:
                    sent = sent + (punct or ".")
                
                result.append(sent)
        
        final_text = " ".join(result)
        
        # Ensure it doesn't end with multiple punctuation
        final_text = re.sub(r'[.!?]{2,}', '.', final_text)
        
        return final_text
