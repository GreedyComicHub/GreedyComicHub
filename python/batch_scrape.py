#!/usr/bin/env python3
"""Batch scrape multiple manga from komiku.org dengan infinite scroll + genre support"""

import logging
import json
import os
import sys
import time
import random
from pathlib import Path
from .scraper_komiku import scrape_komiku_detail, scrape_komiku_manga_list
from .utils import DATA_DIR, write_json, read_json

def batch_scrape(genre=None, resume_from=None, limit=None):
    """Scrape semua manga dari komiku.org, opsional by genre
    
    Args:
        genre: Filter by genre (e.g., 'action', 'horror', 'romance')
        resume_from: Resume dari manga tertentu
        limit: Limit jumlah manga yang di-scrape
    """
    
    # Load existing index.json
    index_file = os.path.join(DATA_DIR, "index.json")
    if os.path.exists(index_file):
        index_data = read_json(index_file)
    else:
        index_data = {}
    
    # Fetch manga list dari website dengan infinite scroll handling
    logging.info("Fetching manga list from komiku.org...")
    manga_list = scrape_komiku_manga_list(genre=genre, limit=limit)
    
    if not manga_list:
        logging.error("Failed to fetch manga list!")
        return
    
    logging.info(f"Found {len(manga_list)} manga to scrape")
    
    total = len(manga_list)
    start_index = 0
    
    if resume_from:
        try:
            start_index = next(i for i, m in enumerate(manga_list) if m['slug'] == resume_from)
            logging.info(f"Resuming from {resume_from} (index {start_index})")
        except StopIteration:
            logging.warning(f"Manga {resume_from} not found in list")
    
    successful = 0
    failed = 0
    skipped = 0
    
    for idx, manga_info in enumerate(manga_list[start_index:], start=start_index + 1):
        try:
            slug = manga_info['slug']
            logging.info(f"\n[{idx}/{total}] Scraping: {slug}")
            
            # Check if already exists in index
            if slug in index_data:
                logging.info(f"  Already exists, skipping...")
                skipped += 1
                continue
            
            # Scrape manga details
            result = scrape_komiku_detail(slug)
            if result:
                # Add to index data
                index_data[slug] = result
                logging.info(f"  Success! Total chapters: {result.get('total_chapters', 0)}")
                successful += 1
            else:
                logging.info(f"  Failed to scrape {slug}")
                failed += 1
            
            # Random delay between scrapes to avoid detection (2-5 seconds)
            delay = random.uniform(2, 5)
            logging.info(f"  Waiting {delay:.1f}s before next scrape...")
            time.sleep(delay)
                
        except Exception as e:
            logging.error(f"  Error scraping {slug}: {e}")
            failed += 1
            continue
    
    # Save updated index.json
    write_json(index_file, index_data)
    logging.info(f"Updated {index_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("BATCH SCRAPE SUMMARY")
    print("="*60)
    print(f"Total:      {total}")
    print(f"Successful: {successful}")
    print(f"Skipped:    {skipped}")
    print(f"Failed:     {failed}")
    print("="*60)
    
    return successful, skipped, failed

if __name__ == "__main__":
    import logging as log_module
    
    # Setup logging
    log_module.basicConfig(
        level=log_module.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    resume_from = sys.argv[1] if len(sys.argv) > 1 else None
    batch_scrape(resume_from=resume_from)
