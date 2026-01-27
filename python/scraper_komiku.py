"""
scraper_komiku.py: Selenium-based scraper untuk komiku.org manga
Handles dynamic content, chapters, dan images dengan retry logic.
Based on actual HTML structure dari komiku.org
"""
import logging
import time
import random
import os
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# User agents untuk rotating
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def _get_driver():
    """Initialize Chrome driver with options."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--disable-web-resources")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Chrome driver initialized")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize Chrome driver: {e}")
        raise

def scrape_komiku_manga_list(genre: Optional[str] = None, limit: Optional[int] = None, max_retries: int = 3) -> List[Dict[str, str]]:
    """
    Scrape manga list dari komiku.org/pustaka/?tipe=manga
    Menggunakan struktur HTML actual dari komiku.org
    Bisa filter by genre atau scrape semua manga.
    
    Args:
        genre: Filter by genre (action, horror, romance, etc) - opsional
        limit: Limit jumlah manga - opsional
        max_retries: Retry attempts jika error
    
    Returns:
        List of dicts dengan {slug, title, url, cover_url}
    """
    logging.info("Starting manga list scrape from komiku.org/pustaka/?tipe=manga")
    driver = None
    
    try:
        driver = _get_driver()
        
        # Build URL with genre filter jika ada
        if genre:
            url = f"https://komiku.org/genre/{genre}/"
            logging.info(f"Scraping manga by genre: {genre}")
        else:
            url = "https://komiku.org/pustaka/?tipe=manga"
            logging.info("Scraping all manga")
        
        driver.get(url)
        logging.info(f"Opened: {url}")
        
        # Wait for content to load - try multiple selectors
        wait = WebDriverWait(driver, 15)
        try:
            # Try common manga link selectors
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.daftar")))
            logging.info("Page loaded with manga content")
        except TimeoutException:
            logging.warning("Timeout on div.daftar, trying alternative selectors...")
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/manga/']")))
                logging.info("Page loaded with manga links (alternative selector)")
            except TimeoutException:
                logging.warning("Could not find expected content, continuing anyway...")
        
        # Give page extra time for dynamic content
        time.sleep(2)
        
        # Scroll to load more if exists (infinite scroll)
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 50 if not limit else min(50, (limit // 10) + 5)  # Adjust scrolls based on limit
        
        while scroll_attempts < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logging.info("Reached end of page")
                break
            last_height = new_height
            scroll_attempts += 1
        
        # Extract manga data - try multiple selectors
        manga_elements = []
        try:
            # Try primary selector
            manga_elements = driver.find_elements(By.CSS_SELECTOR, "div.daftar div.bge a")
            if not manga_elements:
                # Fallback to alternative
                manga_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/manga/']")
        except:
            logging.warning("Could not find manga elements")
            return []
        
        logging.info(f"Found {len(manga_elements)} potential manga links")
        manga_list = []
        
        for elem in manga_elements:
            try:
                href = elem.get_attribute("href")
                if not href or "/manga/" not in href:
                    continue
                    
                slug = href.split("/manga/")[1].rstrip("/").split("/")[0]  # Handle edge cases
                
                # Get title
                title = None
                try:
                    title = elem.find_element(By.CSS_SELECTOR, "h4, .title, .judul").text.strip()
                except:
                    try:
                        title = elem.text.strip()
                    except:
                        title = slug
                
                # Get cover image
                cover_url = None
                try:
                    img = elem.find_element(By.CSS_SELECTOR, "img")
                    cover_url = img.get_attribute("src") or img.get_attribute("data-src")
                except:
                    pass
                
                if slug and title and slug not in [m['slug'] for m in manga_list]:
                    manga_list.append({
                        "slug": slug,
                        "title": title,
                        "url": f"https://komiku.org/manga/{slug}/",
                        "cover_url": cover_url or "N/A"
                    })
                    
                    # Check if reached limit
                    if limit and len(manga_list) >= limit:
                        logging.info(f"Reached limit: {limit} manga")
                        break
                    
                    logging.debug(f"  Added: {slug} - {title}")
            except Exception as e:
                logging.debug(f"  Skipped element: {e}")
                continue
        
        logging.info(f"Extracted {len(manga_list)} manga from list")
        return manga_list
        
    except TimeoutException:
        logging.error("Timeout waiting for page to load")
        return []
    except Exception as e:
        logging.error(f"Error scraping manga list: {e}", exc_info=True)
        return []
    finally:
        if driver:
            driver.quit()
            logging.info("Driver closed")

def scrape_komiku_detail(slug: str, max_retries: int = 3) -> Optional[Dict]:
    """
    Scrape manga detail from https://komiku.org/manga/{slug}/
    Returns format matching index.json structure.
    
    Args:
        slug: Manga slug (e.g., "lostend")
        
    Returns:
        Dict with: title, author, synopsis, cover, genre, type, total_chapters, source_url
    """
    logging.info(f"Starting detail scrape for slug: {slug}")
    driver = None
    
    try:
        driver = _get_driver()
        url = f"https://komiku.org/manga/{slug}/"
        driver.get(url)
        logging.info(f"Opened: {url}")
        
        wait = WebDriverWait(driver, 10)
        
        # Title
        title = None
        try:
            title = driver.find_element(By.CSS_SELECTOR, "h1 span").text.strip()
            logging.info(f"  Title: {title}")
        except:
            try:
                title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
                logging.info(f"  Title (fallback): {title}")
            except:
                logging.warning("  Could not find title")
        
        # Cover image
        cover = None
        try:
            img = driver.find_element(By.CSS_SELECTOR, ".cv img, img[alt*='Bahasa Indonesia']")
            cover = img.get_attribute("src")
            logging.info(f"  Cover: {cover[:50]}...")
        except:
            logging.warning("  Could not find cover image")
        
        # Synopsis
        synopsis = ""
        try:
            synopsis = driver.find_element(By.CSS_SELECTOR, "p.desc, #Sinopsis p").text.strip()
            logging.info(f"  Synopsis: {sinopsis[:100]}...")
        except:
            logging.warning("  Could not find synopsis")
        
        # Genre (as single string, comma-separated like in index.json)
        genres = []
        try:
            genre_elements = driver.find_elements(By.CSS_SELECTOR, "ul.genre li, .genre li")
            genres = [li.text.strip() for li in genre_elements if li.text.strip()]
            genre_str = ", ".join(genres) if genres else "Unknown"
            logging.info(f"  Genre: {genre_str}")
        except:
            genre_str = "Unknown"
            logging.warning("  Could not find genres")
        
        # Type (Manga/Manhua/Manhwa)
        manga_type = "Manga"  # Default
        try:
            type_cell = driver.find_element(By.CSS_SELECTOR, "table.inftable td:contains('Jenis Komik') + td")
            manga_type = type_cell.text.strip()
            logging.info(f"  Type: {manga_type}")
        except:
            # Try alternative selector
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "table.inftable tr")
                for row in rows:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    if len(cells) >= 2 and "Jenis Komik" in cells[0].text:
                        manga_type = cells[1].text.strip()
                        logging.info(f"  Type: {manga_type}")
                        break
            except:
                logging.warning("  Could not find manga type")
        
        # Extract chapter count from the table
        total_chapters = 0
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table#Daftar_Chapter tbody tr")))
            chapter_rows = driver.find_elements(By.CSS_SELECTOR, "table#Daftar_Chapter tbody tr")
            total_chapters = len([r for r in chapter_rows if r.find_elements(By.CSS_SELECTOR, "td")])
            logging.info(f"  Found {total_chapters} chapters")
        except Exception as e:
            logging.warning(f"  Could not extract chapter count: {e}")
        
        # Author - extract from table if available
        author = "Unknown"
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "table.inftable tr")
            for row in rows:
                cells = row.find_elements(By.CSS_SELECTOR, "td")
                if len(cells) >= 2 and "Pengarang" in cells[0].text:
                    author = cells[1].text.strip()
                    logging.info(f"  Author: {author}")
                    break
        except:
            logging.warning("  Could not find author")
        
        result = {
            "title": title or "Unknown",
            "author": author,
            "synopsis": synopsis,
            "cover": cover or "N/A",
            "genre": genre_str,
            "type": manga_type,
            "total_chapters": total_chapters,
            "source_url": url
        }
        
        logging.info(f"Detail scrape completed for {slug}")
        return result
        
    except Exception as e:
        logging.error(f"✗ Error scraping detail for {slug}: {e}", exc_info=True)
        return None
    finally:
        if driver:
            driver.quit()

def scrape_komiku_chapter(chapter_url: str) -> List[str]:
    """
    Scrape chapter images from chapter page.
    
    Args:
        chapter_url: Chapter URL (e.g., https://komiku.org/slug-chapter-1/)
        
    Returns:
        List of image URLs (hotlinks only, no download)
    """
    logging.info(f"Starting chapter scrape: {chapter_url[:80]}...")
    driver = None
    
    try:
        driver = _get_driver()
        driver.get(chapter_url)
        logging.info(f"Opened chapter page")
        
        wait = WebDriverWait(driver, 10)
        
        # Wait for images to load
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div#Baca_Komik img.klazy, div#Baca_Komik img")))
        logging.info("✓ Chapter page loaded")
        
        # Extract image URLs
        image_elements = driver.find_elements(By.CSS_SELECTOR, "div#Baca_Komik img.klazy, div#Baca_Komik img")
        image_urls = []
        
        for img in image_elements:
            try:
                src = img.get_attribute("src")
                if src and src.startswith("http"):
                    image_urls.append(src)
                    logging.debug(f"  Image: {src[:60]}...")
            except:
                continue
        
        logging.info(f"✓ Extracted {len(image_urls)} images from chapter")
        return image_urls
        
    except Exception as e:
        logging.error(f"✗ Error scraping chapter: {e}", exc_info=True)
        return []
    finally:
        if driver:
            driver.quit()

def test_scraper():
    """Test scraper with one manga slug."""
    logging.info("=" * 60)
    logging.info("SCRAPER TEST")
    logging.info("=" * 60)
    
    # Test detail scrape with a known manga
    test_slug = "lostend"
    logging.info(f"\nTesting detail scrape with slug: {test_slug}")
    detail = scrape_komiku_detail(test_slug)
    
    if detail:
        print(f"\n✓ Detail scrape successful!")
        print(f"  Title: {detail['title']}")
        print(f"  Genres: {', '.join(detail['genres'])}")
        print(f"  Chapters: {len(detail['chapters'])}")
        
        # Test chapter scrape with first chapter if available
        if detail['chapters']:
            first_chapter = detail['chapters'][0]
            logging.info(f"\nTesting chapter scrape: {first_chapter['number']}")
            images = scrape_komiku_chapter(first_chapter['url'])
            print(f"✓ Chapter scrape successful! Found {len(images)} images")
            if images:
                print(f"  First image: {images[0][:80]}...")
    else:
        print(f"✗ Detail scrape failed")

if __name__ == "__main__":
    test_scraper()
