#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Komiku.org Manga Scraper
Scrape manga data, chapters, and images from komiku.org
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
from datetime import datetime
from pathlib import Path
import re
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
BASE_URL = "https://komiku.org"
DATA_DIR = "data"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Synonym map for paraphrasing
PARAPHRASE_MAP = {
    'wanita': ['perempuan', 'gadis', 'putri'],
    'muda': ['remaja', 'belia', 'putra'],
    'cerita': ['kisah', 'tale', 'narasi', 'plot'],
    'hidup': ['kehidupan', 'eksistensi', 'keberadaan'],
    'diri': ['dirinya', 'pribadi', 'self'],
    'menjadi': ['berubah menjadi', 'bertransformasi', 'menjadi'],
    'memiliki': ['punya', 'mempunyai', 'memiliki'],
    'dunia': ['alam', 'realm', 'dimensi'],
    'kekuatan': ['power', 'kemampuan', 'kekuatan supernatural'],
    'musuh': ['lawan', 'antagonis', 'musuh tajam'],
    'teman': ['sahabat', 'kawan', 'sekutu'],
    'mencari': ['mengais', 'mencari-cari', 'memburu'],
    'menemukan': ['meraih', 'mendapatkan', 'menemukan'],
}

def delay():
    """Human-like delay between requests"""
    time.sleep(random.uniform(0.5, 1.5))

def paraphrase_synopsis(text):
    """Paraphrase synopsis by replacing words with synonyms"""
    if not text:
        return ""
    
    words = text.split()
    paraphrased = []
    
    for word in words:
        word_lower = word.lower()
        # Simple replacement: 30% chance if word is in map
        if word_lower in PARAPHRASE_MAP and random.random() < 0.3:
            replacement = random.choice(PARAPHRASE_MAP[word_lower])
            # Maintain capitalization
            if word[0].isupper():
                paraphrased.append(replacement.capitalize())
            else:
                paraphrased.append(replacement)
        else:
            paraphrased.append(word)
    
    return ' '.join(paraphrased)

def ensure_data_dir():
    """Create data directory if not exists"""
    Path(DATA_DIR).mkdir(exist_ok=True)

def get_manga_list(limit=None):
    """Scrape list of manga from komiku.org daftar-komik"""
    manga_list = []
    halaman = 1
    max_pages = 5  # Start with 5 pages for testing
    
    print("[*] Scraping manga list (limit: {})...".format(limit))
    
    try:
        while halaman <= max_pages:
            if limit and len(manga_list) >= limit:
                break
            
            # Try with halaman parameter
            url = "{}/daftar-komik/?tipe=manga&halaman={}".format(BASE_URL, halaman)
            print("    [>] Page {}: {}".format(halaman, url))
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print("    [!] Error on page {}: {}".format(halaman, e))
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find manga grid
            grid = soup.find('div', class_='manga-grid')
            if not grid:
                print("    [!] No manga-grid found on page {}".format(halaman))
                break
            
            # Find all articles
            articles = grid.find_all('article', class_='manga-card')
            print("    [*] Found {} manga on page {}".format(len(articles), halaman))
            
            if not articles:
                break
            
            for article in articles:
                if limit and len(manga_list) >= limit:
                    break
                
                try:
                    # Get link
                    link = article.find('a', href=re.compile(r'/manga/'))
                    if not link:
                        continue
                    
                    href = link.get('href', '')
                    slug = href.strip('/').split('/')[-1]
                    
                    # Get title
                    h4 = article.find('h4')
                    if h4:
                        title_link = h4.find('a')
                        title = title_link.text.strip() if title_link else "Unknown"
                    else:
                        title = "Unknown"
                    
                    # Get meta info (genre, status)
                    meta = article.find('p', class_='meta')
                    status = "Unknown"
                    if meta:
                        meta_text = meta.text
                        if 'Ongoing' in meta_text:
                            status = "Ongoing"
                        elif 'Completed' in meta_text or 'Tamat' in meta_text:
                            status = "Completed"
                    
                    # Get thumbnail
                    img = article.find('img', class_='lazy')
                    cover = ""
                    if img:
                        cover = img.get('data-src', img.get('src', ''))
                    
                    manga_list.append({
                        'slug': slug,
                        'title': title,
                        'url': "{}/manga/{}/".format(BASE_URL, slug),
                        'status': status,
                        'cover': cover
                    })
                    
                except Exception as e:
                    print("    [!] Error parsing manga: {}".format(e))
                    continue
            
            delay()
            halaman += 1
        
        print("[*] Total manga found: {}".format(len(manga_list)))
        return manga_list
    
    except Exception as e:
        print("[!] Error scraping manga list: {}".format(e))
        return manga_list

def get_manga_detail(url, slug):
    """Scrape manga detail page"""
    print("  [>] Scraping detail: {}".format(slug))
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("  [!] Error fetching {}: {}".format(url, e))
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {
        'title': 'Unknown',
        'alternative_title': '',
        'type': 'Manga',
        'genres': [],
        'author': '',
        'status': 'Unknown',
        'synopsis': '',
        'chapters': []
    }
    
    # Get title
    h1 = soup.find('h1')
    if h1:
        span = h1.find('span')
        if span:
            data['title'] = span.text.strip()
    
    # Get genres
    genre_list = soup.find('ul', class_='genre')
    if genre_list:
        for li in genre_list.find_all('li'):
            span = li.find('span')
            if span:
                data['genres'].append(span.text.strip())
    
    # Get author, status, alternative title from table
    table = soup.find('table', class_='inftable')
    if table:
        rows = table.find_all('tr')
        for row in rows:
            tds = row.find_all('td')
            if len(tds) >= 2:
                label = tds[0].text.strip().lower()
                value = tds[1].text.strip()
                
                if 'pengarang' in label:
                    data['author'] = value
                elif 'status' in label:
                    if 'tamat' in value.lower() or 'completed' in value.lower():
                        data['status'] = 'Completed'
                    elif 'ongoing' in value.lower():
                        data['status'] = 'Ongoing'
                    else:
                        data['status'] = value
                elif 'judul indonesia' in label or 'judul lain' in label:
                    data['alternative_title'] = value
    
    # Get synopsis
    synopsis_section = soup.find('section', id='Sinopsis')
    if synopsis_section:
        paragraphs = synopsis_section.find_all('p')
        synopsis_text = ' '.join([p.text.strip() for p in paragraphs])
        data['synopsis'] = paraphrase_synopsis(synopsis_text)
    
    # Get chapters
    chapters_table = soup.find('table', id='Daftar_Chapter')
    if chapters_table:
        tbody = chapters_table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            for row in rows:
                try:
                    td = row.find('td', class_='judulseries')
                    if not td:
                        continue
                    
                    link = td.find('a')
                    if not link:
                        continue
                    
                    chapter_url = link.get('href', '')
                    if not chapter_url:
                        continue
                    
                    chapter_text = link.text.strip()
                    # Extract chapter number
                    match = re.search(r'Chapter\s+([\d.]+)', chapter_text, re.IGNORECASE)
                    if match:
                        chapter_num = match.group(1)
                    else:
                        chapter_num = chapter_text
                    
                    # Make absolute URL
                    if not chapter_url.startswith('http'):
                        chapter_url = "{}{}".format(BASE_URL, chapter_url)
                    
                    data['chapters'].append({
                        'number': chapter_num,
                        'url': chapter_url,
                        'images': []
                    })
                except Exception as e:
                    print("  [!] Error parsing chapter: {}".format(e))
                    continue
    
    delay()
    return data

def get_chapter_images(chapter_url, chapter_num):
    """Scrape images from chapter page"""
    try:
        response = requests.get(chapter_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("    [!] Error fetching chapter {}: {}".format(chapter_num, e))
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    images = []
    
    # Find image container
    baca_komik = soup.find('div', id='Baca_Komik')
    if baca_komik:
        img_tags = baca_komik.find_all('img', class_='klazy')
        for img in img_tags:
            src = img.get('src', img.get('data-src', ''))
            if src:
                # Make absolute URL
                if not src.startswith('http'):
                    src = "{}{}".format(BASE_URL, src)
                images.append(src)
    
    delay()
    return images

def save_manga_data(data, slug):
    """Save manga data to JSON file"""
    filepath = os.path.join(DATA_DIR, "{}.json".format(slug))
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("  [*] Saved: {}".format(filepath))
    except Exception as e:
        print("  [!] Error saving {}: {}".format(slug, e))

def update_index(manga_list):
    """Update index.json with manga list"""
    index_path = os.path.join(DATA_DIR, 'index.json')
    
    try:
        # Load existing index
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {}
        
        # Update with new manga
        for manga in manga_list:
            slug = manga['slug']
            if slug not in index:
                index[slug] = {
                    'title': manga['title'],
                    'status': manga['status'],
                    'type': 'Manga',
                    'last_scraped': datetime.now().strftime('%Y-%m-%d')
                }
        
        # Save index
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        print("[*] Index updated: {}".format(index_path))
    
    except Exception as e:
        print("[!] Error updating index: {}".format(e))

def main():
    """Main scraping function"""
    print("\n" + "="*60)
    print("  KOMIKU.ORG MANGA SCRAPER")
    print("="*60 + "\n")
    
    ensure_data_dir()
    
    # Scrape manga list
    limit = 20  # Change this to scrape more (or None for all)
    manga_list = get_manga_list(limit=limit)
    
    if not manga_list:
        print("[!] No manga found. Exiting.")
        return
    
    print("\n[*] Scraping details for {} manga...\n".format(len(manga_list)))
    
    successful = 0
    failed = 0
    
    for idx, manga in enumerate(manga_list, 1):
        try:
            print("[{}/{}] {}".format(idx, len(manga_list), manga['title']))
            
            # Get detail
            detail = get_manga_detail(manga['url'], manga['slug'])
            if not detail:
                failed += 1
                continue
            
            # Scrape chapters
            print("  [>] Scraping {} chapters...".format(len(detail['chapters'])))
            for chapter in detail['chapters'][:10]:  # Limit to 10 chapters per manga for testing
                images = get_chapter_images(chapter['url'], chapter['number'])
                chapter['images'] = images
                print("    [*] Chapter {}: {} images".format(chapter['number'], len(images)))
            
            # Save to JSON
            save_manga_data(detail, manga['slug'])
            successful += 1
            
        except Exception as e:
            print("[!] Error processing {}: {}".format(manga['title'], e))
            failed += 1
        
        print()
    
    # Update index
    update_index(manga_list)
    
    # Summary
    print("="*60)
    print("Scraping selesai.")
    print("Total manga: {}".format(len(manga_list)))
    print("Successful: {}".format(successful))
    print("Failed: {}".format(failed))
    print("Data saved di folder: {}/".format(DATA_DIR))
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
