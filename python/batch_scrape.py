#!/usr/bin/env python3
"""Batch scrape multiple manga from komiku.org"""

import logging
import json
import os
import sys
from pathlib import Path
from .scraper_komiku import scrape_komiku_detail
from .utils import DATA_DIR, write_json, read_json

def get_manga_list(search_term=None):
    """Get list of manga slugs to scrape from index.json or user input"""
    index_file = os.path.join(DATA_DIR, "index.json")
    
    if os.path.exists(index_file):
        try:
            index_data = read_json(index_file)
            if isinstance(index_data, list):
                slugs = [item.get("slug") for item in index_data if item.get("slug")]
                logging.info(f"Found {len(slugs)} manga in index.json")
                return slugs
        except Exception as e:
            logging.warning(f"Could not read index.json: {e}")
    
    # Default manga list if index not available
    default_manga = [
        "dandadan", "solo-leveling-id", "lostend", "blue-lock",
        "kimetsu-no-yaiba-indonesia", "komik-one-piece-indo",
        "shuumatsu-no-valkyrie-indonesia", "kingdom", "nano-machine",
        "magic-emperor", "return-of-the-legend", "kill-the-dragon"
    ]
    
    logging.info(f"Using default manga list: {len(default_manga)} titles")
    return default_manga

def batch_scrape(manga_list=None, resume_from=None):
    """Scrape multiple manga in batch"""
    
    if manga_list is None:
        manga_list = get_manga_list()
    
    total = len(manga_list)
    start_index = 0
    
    if resume_from:
        try:
            start_index = manga_list.index(resume_from)
            logging.info(f"Resuming from {resume_from} (index {start_index})")
        except ValueError:
            logging.warning(f"Manga {resume_from} not found in list")
    
    successful = 0
    failed = 0
    skipped = 0
    
    for idx, slug in enumerate(manga_list[start_index:], start=start_index + 1):
        try:
            logging.info(f"\n[{idx}/{total}] Scraping: {slug}")
            
            # Check if already exists
            comic_file = os.path.join(DATA_DIR, f"{slug}.json")
            if os.path.exists(comic_file):
                logging.info(f"  Already exists, skipping...")
                skipped += 1
                continue
            
            # Scrape manga details
            result = scrape_komiku_detail(slug)
            if result:
                write_json(comic_file, result)
                logging.info(f"  Success! Saved {len(result.get('chapters', []))} chapters")
                successful += 1
            else:
                logging.warning(f"  Failed to scrape {slug}")
                failed += 1
                
        except Exception as e:
            logging.error(f"  Error scraping {slug}: {e}")
            failed += 1
            continue
    
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
