#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Komiku.org Manga Scraper
Scrapes manga list, details, chapters, and images from komiku.org
Focus: tipe=manga only
"""

import json
import os
import re
import random
import time
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://komiku.org"
MANGA_LIST_URL = f"{BASE_URL}/daftar-komik/?tipe=manga"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
DATA_DIR = "data"
LIMIT = None  # Change to larger number for testing or specific number (5, 20, 50, etc.)

# Synonyms dictionary for paraphrasing
SYNONYMS = {
    'wanita': 'cewek',
    'wanita muda': 'gadis',
    'muda': 'remaja',
    'anak': 'bocah',
    'anak muda': 'pemuda',
    'pemuda': 'anak laki',
    'berat': 'gemuk',
    'badan': 'tubuh',
    'tubuh': 'badan',
    'percaya diri': 'pede',
    'perjalanan': 'petualangan',
    'petualangan': 'jalan',
    'menurunkan': 'ngecilin',
    'cerita': 'kisah',
    'mengikuti': 'ngeikutin',
    'melawan': 'hadapi',
    'menghadapi': 'melawan',
    'kekuatan': 'kekuatan magis',
    'dunia': 'alam',
    'alam': 'dunia',
    'tiba-tiba': 'tiba2',
    'mendapat': 'dapet',
    'kehidupan': 'hidup',
    'hidup': 'kehidupan',
    'kehidupan baru': 'awal baru',
    'kembali': 'balik',
    'balik': 'kembali',
    'menghilang': 'hilang',
    'disebut': 'dipanggil',
    'dipanggil': 'disebut',
    'hebat': 'kuat',
    'kuat': 'powerful',
    'ingin': 'pengen',
    'pengen': 'ingin',
    'terbang': 'terbang tinggi',
    'bertemu': 'ketemu',
    'ketemu': 'bertemu',
    'membunuh': 'bunuh',
    'bunuh': 'membunuh',
    'seni': 'teknik',
    'teknik': 'seni',
    'bela diri': 'martial arts',
    'martial arts': 'bela diri',
    'perkara': 'masalah',
    'masalah': 'perkara',
    'raksasa': 'giant',
    'makhluk': 'monster',
    'monster': 'makhluk',
}

CASUAL_SUFFIXES = [
    " bro!",
    " nih!",
    " gitu loh!",
    " gampang aja!",
    " mantap!",
    " asik!",
    " oke deh!",
]


def delay():
    """Add random delay between requests"""
    time.sleep(random.uniform(2, 4))


def paraphrase(text: str) -> str:
    """
    Paraphrase text by replacing 20-40% of words with synonyms
    and adding casual Indonesian suffixes
    """
    if not text:
        return text
    
    words = text.split()
    replacement_count = max(1, int(len(words) * random.uniform(0.2, 0.4)))
    indices_to_replace = random.sample(range(len(words)), min(replacement_count, len(words)))
    
    for idx in indices_to_replace:
        word = words[idx].lower().strip('.,!?;:')
        if word in SYNONYMS:
            words[idx] = SYNONYMS[word]
    
    result = ' '.join(words)
    result += random.choice(CASUAL_SUFFIXES)
    return result


def extract_chapter_number(chapter_text: str) -> str:
    """Extract chapter number from text like 'Chapter 1', 'Chapter 2.5'"""
    match = re.search(r'(\d+(?:\.\d+)?)', chapter_text)
    if match:
        return match.group(1)
    return chapter_text.strip()


def get_manga_list(page: int = 1) -> Tuple[List[Dict], Optional[int]]:
    """
    Fetch manga list from komiku.org
    Returns: (list of manga dict with slug/title, next_page or None)
    """
    url = f"{MANGA_LIST_URL}&halaman={page}" if page > 1 else MANGA_LIST_URL
    
    try:
        print(f"[LIST] Fetching page {page}: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        manga_list = []
        manga_grid = soup.find('div', class_='manga-grid')
        
        if not manga_grid:
            print(f"[ERROR] Manga grid not found on page {page}")
            return [], None
        
        articles = manga_grid.find_all('article', class_='manga-card')
        print(f"[LIST] Found {len(articles)} manga on page {page}")
        
        for article in articles:
            link = article.find('a', href=True)
            if not link:
                continue
            
            href = link['href']
            # Extract slug from /manga/slug/ or manga/slug/ format
            if '/manga/' in href:
                slug = href.split('/manga/')[-1].strip('/')
            else:
                continue
            
            if not slug:
                continue
            
            title_elem = article.find('h3') or article.find('a')
            title = title_elem.get_text(strip=True) if title_elem else slug
            
            cover_img = article.find('img')
            cover = cover_img.get('src', '') if cover_img else ''
            if cover and not cover.startswith('http'):
                cover = f"{BASE_URL}{cover}"
            
            manga_list.append({
                'slug': slug,
                'title': title,
                'cover': cover,
                'source_url': f"{BASE_URL}/manga/{slug}/"
            })
        
        # Check for next page
        next_page = None
        pagination = soup.find('ul', class_=re.compile('paginasi|pagination', re.I))
        if pagination:
            next_link = pagination.find('a', text=re.compile('>|next', re.I))
            if next_link:
                next_page = page + 1
        
        delay()
        return manga_list, next_page
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch manga list page {page}: {e}")
        return [], None


def get_detail(slug: str) -> Optional[Dict]:
    """
    Fetch manga detail page
    Returns: dict with title, author, genres, synopsis, etc.
    """
    url = f"{BASE_URL}/manga/{slug}/"
    
    try:
        print(f"  [DETAIL] Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else slug
        
        # Cover image - try to find high-quality version
        cover = ''
        cover_img = soup.find('img', class_=re.compile('komik-thumb|cover|thumb', re.I))
        if not cover_img:
            cover_parent = soup.find('div', class_=re.compile('cover', re.I))
            cover_img = cover_parent.find('img') if cover_parent else None
        
        if cover_img:
            cover = cover_img.get('src', '') or cover_img.get('data-src', '')
            if cover and not cover.startswith('http'):
                cover = f"{BASE_URL}{cover}"
        
        # Genre from table or ul
        genres = []
        info_table = soup.find('table', class_=re.compile('inftable|infotable', re.I))
        if info_table:
            for row in info_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    header = cells[0].get_text(strip=True).lower()
                    if 'genre' in header or 'kategori' in header:
                        genre_links = cells[1].find_all('a')
                        genres = [g.get_text(strip=True) for g in genre_links]
                        break
        
        if not genres:
            genre_ul = soup.find('ul', class_=re.compile('genre', re.I))
            if genre_ul:
                genre_items = genre_ul.find_all('li')
                genres = [g.get_text(strip=True) for g in genre_items]
        
        # Author from table
        author = ''
        if info_table:
            for row in info_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    header = cells[0].get_text(strip=True).lower()
                    if 'penulis' in header or 'author' in header:
                        author = cells[1].get_text(strip=True)
                        break
        
        # Status from table
        status = 'Unknown'
        if info_table:
            for row in info_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    header = cells[0].get_text(strip=True).lower()
                    if 'status' in header:
                        status = cells[1].get_text(strip=True)
                        break
        
        # Synopsis - get full text
        synopsis = ''
        synopsis_section = soup.find('div', class_=re.compile('sinopsis|synopsis|description', re.I))
        if not synopsis_section:
            for elem in soup.find_all(['p', 'div']):
                text = elem.get_text(strip=True).lower()
                if 'sinopsis' in text or 'deskripsi' in text:
                    synopsis_section = elem.parent
                    break
        
        if synopsis_section:
            paragraphs = synopsis_section.find_all('p')
            if paragraphs:
                synopsis = ' '.join([p.get_text(strip=True) for p in paragraphs])
            else:
                synopsis = synopsis_section.get_text(strip=True)
        
        # Clean synopsis
        synopsis = re.sub(r'Sinopsis[:\s]*', '', synopsis, flags=re.I).strip()
        
        detail = {
            'title': title,
            'author': author,
            'genre': ', '.join(genres) if genres else '',
            'status': status,
            'synopsis': synopsis,
            'cover': cover,
            'source_url': url
        }
        
        delay()
        return detail
    
    except Exception as e:
        print(f"  [ERROR] Failed to fetch detail for {slug}: {e}")
        return None


def get_chapter_images(chapter_url: str) -> List[str]:
    """
    Fetch all images from a chapter page
    Returns: list of image URLs
    """
    try:
        print(f"    [IMAGES] Fetching: {chapter_url}")
        response = requests.get(chapter_url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        images = []
        
        # Try to find images in various containers
        image_containers = [
            soup.find('div', id=re.compile('Baca_Komik|baca-komik|chapter-content', re.I)),
            soup.find('div', class_=re.compile('chapter-content|images|viewer', re.I)),
        ]
        
        for container in image_containers:
            if container:
                imgs = container.find_all('img', class_=re.compile('klazy|lazy|image', re.I))
                for img in imgs:
                    src = img.get('src', '') or img.get('data-src', '')
                    if src and ('img' in src or 'image' in src or 'komiku' in src):
                        if not src.startswith('http'):
                            src = f"{BASE_URL}{src}"
                        images.append(src)
                
                if images:
                    break
        
        # Fallback: get all images in body
        if not images:
            all_imgs = soup.find_all('img')
            for img in all_imgs:
                src = img.get('src', '') or img.get('data-src', '')
                if src and ('uploads' in src or 'img' in src):
                    if not src.startswith('http'):
                        src = f"{BASE_URL}{src}"
                    if src not in images:
                        images.append(src)
        
        print(f"    [IMAGES] Found {len(images)} images")
        delay()
        return images
    
    except Exception as e:
        print(f"    [ERROR] Failed to fetch images from {chapter_url}: {e}")
        return []


def get_chapters(slug: str) -> Dict[str, Dict]:
    """
    Fetch all chapters for a manga
    Returns: dict with chapter_number as key
    """
    url = f"{BASE_URL}/manga/{slug}/"
    chapters = {}
    
    try:
        print(f"  [CHAPTERS] Fetching chapter list for {slug}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find chapter table
        chapter_table = soup.find('table', id=re.compile('Daftar_Chapter|chapter', re.I))
        if not chapter_table:
            print(f"  [WARN] No chapter table found for {slug}")
            return {}
        
        rows = chapter_table.find_all('tr')
        chapter_count = 0
        
        for row in rows[1:]:  # Skip header
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
            
            # Chapter title and link
            link = cells[0].find('a', href=True)
            if not link:
                continue
            
            chapter_title = link.get_text(strip=True)
            chapter_url = link['href']
            
            if not chapter_url.startswith('http'):
                chapter_url = f"{BASE_URL}{chapter_url}"
            
            # Extract chapter number
            chapter_num = extract_chapter_number(chapter_title)
            
            # Get images for this chapter
            images = get_chapter_images(chapter_url)
            
            chapters[chapter_num] = {
                'title': chapter_title,
                'url': chapter_url,
                'images': images
            }
            
            chapter_count += 1
        
        print(f"  [CHAPTERS] Found {chapter_count} chapters for {slug}")
        delay()
        return chapters
    
    except Exception as e:
        print(f"  [ERROR] Failed to fetch chapters for {slug}: {e}")
        return {}


def save_manga_data(slug: str, detail: Dict, chapters: Dict):
    """Save manga data to JSON file"""
    if not detail:
        return False
    
    try:
        # Prepare full data with paraphrased synopsis
        full_synopsis = paraphrase(detail.get('synopsis', '')) if detail.get('synopsis') else ''
        
        manga_data = {
            'title': detail.get('title', ''),
            'author': detail.get('author', ''),
            'genre': detail.get('genre', ''),
            'synopsis': full_synopsis,
            'cover': detail.get('cover', ''),
            'source_url': detail.get('source_url', ''),
            'chapters': chapters
        }
        
        # Save to data/{slug}.json
        file_path = os.path.join(DATA_DIR, f"{slug}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(manga_data, f, ensure_ascii=False, indent=2)
        
        print(f"[SAVE] Saved {slug}.json")
        return True
    
    except Exception as e:
        print(f"[ERROR] Failed to save {slug}.json: {e}")
        return False


def update_index(index: Dict, slug: str, detail: Dict, chapters: Dict):
    """Update index.json with manga summary"""
    if not detail:
        return index
    
    # Short synopsis for index (truncate)
    short_synopsis = detail.get('synopsis', '')
    if len(short_synopsis) > 250:
        short_synopsis = short_synopsis[:250] + '...'
    
    index[slug] = {
        'title': detail.get('title', ''),
        'author': detail.get('author', ''),
        'synopsis': short_synopsis,
        'cover': detail.get('cover', ''),
        'genre': detail.get('genre', ''),
        'type': 'Manga',
        'total_chapters': len(chapters),
        'source_url': detail.get('source_url', '')
    }
    
    return index


def load_existing_index() -> Dict:
    """Load existing index.json if available"""
    index_path = os.path.join(DATA_DIR, 'index.json')
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_index(index: Dict):
    """Save index.json"""
    try:
        index_path = os.path.join(DATA_DIR, 'index.json')
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        print(f"\n[SAVE] Updated index.json with {len(index)} manga")
    except Exception as e:
        print(f"[ERROR] Failed to save index.json: {e}")


def main():
    """Main scraping function"""
    # Create data directory
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"[SETUP] Created {DATA_DIR} directory")
    
    # Load existing index
    index = load_existing_index()
    print(f"[SETUP] Loaded existing index with {len(index)} entries")
    
    # Scrape all manga pages
    all_manga = []
    page = 1
    
    while True:
        manga_list, next_page = get_manga_list(page)
        if not manga_list:
            break
        
        all_manga.extend(manga_list)
        
        # Check limit
        if LIMIT and len(all_manga) >= LIMIT:
            all_manga = all_manga[:LIMIT]
            break
        
        if next_page is None:
            break
        
        page = next_page
    
    print(f"\n[SCRAPE] Total manga to process: {len(all_manga)}")
    
    # Process each manga
    for idx, manga_item in enumerate(all_manga, 1):
        slug = manga_item['slug']
        print(f"\n[{idx}/{len(all_manga)}] Processing: {slug}")
        
        # Get detail (always fetch for freshness or use LIMIT to test)
        detail = get_detail(slug)
        if not detail:
            print(f"  [WARN] Skipping {slug} - failed to get details")
            continue
        
        # Get chapters
        chapters = get_chapters(slug)
        
        # Save manga data
        save_manga_data(slug, detail, chapters)
        
        # Update index
        index = update_index(index, slug, detail, chapters)
    
    # Save final index
    save_index(index)
    
    print(f"\n[OK] Selesai! Total manga: {len(index)} | File di data/index.json dan data/*.json")


if __name__ == '__main__':
    main()
