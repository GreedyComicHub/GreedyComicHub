#!/usr/bin/env python3
import argparse
import sys
import logging
import time
import random
from pathlib import Path
from urllib.parse import urlparse

from python.scraper import KomikuScraper
from python.data_manager import DataManager

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class GreedyComicHub:
    def __init__(self):
        self.scraper = KomikuScraper()
        self.data_manager = DataManager()
    
    def scrape_manga(self, url=None, manga_type="manga", limit=None):
        """
        Scrape manga - if URL provided, scrape that manga; otherwise scrape all
        
        Args:
            url: Specific manga URL (optional)
            manga_type: Type of manga to scrape (manga, manhua, manhwa)
            limit: Maximum number of manga to scrape
        """
        if url:
            # Scrape specific manga from URL
            self._scrape_single_manga(url)
        else:
            # Scrape all manga of specified type
            self._scrape_all_manga(manga_type, limit)
    
    def _scrape_single_manga(self, url):
        """Scrape a single manga from URL"""
        # Extract slug from URL
        slug = url.rstrip("/").split("/")[-1]
        
        logger.info(f"Scraping manga: {slug}")
        
        try:
            # Check if already exists and load existing synopsis
            existing_synopsis = ""
            if self.data_manager.manga_exists(slug):
                existing_data = self.data_manager.load_manga(slug)
                if existing_data and "synopsis" in existing_data:
                    existing_synopsis = existing_data["synopsis"]
                logger.info(f"Updating existing manga: {slug}")
            
            # Scrape detail
            detail = self.scraper.scrape_manga_detail(url)
            
            # Use existing synopsis if new one is not good
            synopsis_to_use = detail["synopsis"]
            if not synopsis_to_use or len(synopsis_to_use) < 50 or "Daftar Chapter" in synopsis_to_use:
                if existing_synopsis:
                    logger.info(f"Using existing synopsis for {slug}")
                    synopsis_to_use = existing_synopsis
                else:
                    logger.warning(f"No good synopsis found for {slug}")
                    synopsis_to_use = f"Manga: {detail['title']}"
            
            # Scrape all chapters
            chapters = {}
            for ch_title, ch_url in detail["chapter_links"].items():
                try:
                    images = self.scraper.scrape_chapter_images(ch_url)
                    
                    # Extract chapter number
                    ch_num = self._extract_chapter_number(ch_title)
                    
                    chapters[ch_num] = {
                        "title": ch_title,
                        "url": ch_url,
                        "images": images
                    }
                    
                    logger.info(f"  Scraped: {ch_title} ({len(images)} images)")
                    
                    # Human delay between chapters
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.error(f"Error scraping chapter {ch_title}: {e}")
            
            # Paraphrase synopsis
            synopsis_paraphrased = self.scraper.paraphrase_synopsis(synopsis_to_use)
            
            # Prepare manga data
            manga_data = {
                "title": detail["title"],
                "author": detail["author"],
                "genre": detail["genre"],
                "type": detail["type"],
                "cover": detail["cover"],
                "synopsis": synopsis_to_use,  # Original for storage
                "source_url": url,
                "total_chapters": len(chapters),
                "chapters": chapters
            }
            
            # Save to data manager (paraphrased version)
            self.data_manager.add_or_update_manga(slug, manga_data, synopsis_paraphrased)
            
            logger.info(f"✓ Scraped {slug}: {len(chapters)} chapters")
            
        except Exception as e:
            logger.error(f"Failed to scrape {slug}: {e}")
            raise
    
    def _scrape_all_manga(self, manga_type="manga", limit=None):
        """Scrape all manga of specified type"""
        logger.info(f"Scraping manga (type: {manga_type}, limit: {limit if limit else 'unlimited'})")
        
        try:
            # Get manga list with limit
            manga_list = self.scraper.scrape_manga_list(manga_type, limit=limit)
            
            successful = 0
            skipped = 0
            failed = 0
            
            for manga in manga_list:
                slug = manga["slug"]
                url = manga["url"]
                
                # Check if already exists
                if self.data_manager.manga_exists(slug):
                    logger.info(f"⊘ {slug} already exists - skipping")
                    skipped += 1
                    continue
                
                try:
                    self._scrape_single_manga(url)
                    successful += 1
                    time.sleep(random.uniform(3, 6))
                except Exception as e:
                    logger.error(f"✗ Failed to scrape {slug}: {e}")
                    failed += 1
                    time.sleep(random.uniform(2, 4))
            
            logger.info(f"\n=== Summary ===")
            logger.info(f"Total: {len(manga_list)}")
            logger.info(f"Successful: {successful}")
            logger.info(f"Skipped: {skipped}")
            logger.info(f"Failed: {failed}")
            
        except Exception as e:
            logger.error(f"Error scraping manga list: {e}")
            raise
    
    def update_chapters(self, url=None):
        """
        Update chapters for manga(s)
        If URL provided: update that manga (recheck all chapters)
        If no URL: update all registered manga with new chapters only
        """
        if url:
            self._update_manga_chapters(url, check_all=True)
        else:
            self._update_all_manga_chapters()
    
    def _update_manga_chapters(self, url, check_all=False):
        """Update chapters for a specific manga"""
        slug = url.rstrip("/").split("/")[-1]
        logger.info(f"Updating chapters for: {slug}")
        
        try:
            # Scrape detail to get all chapter links
            detail = self.scraper.scrape_manga_detail(url)
            
            # Load existing manga data
            existing_manga = self.data_manager.load_manga(slug)
            if not existing_manga:
                logger.warning(f"{slug} not found in database. Scraping from scratch...")
                self._scrape_single_manga(url)
                return
            
            existing_chapters = existing_manga.get("chapters", {})
            
            if check_all:
                # Scrape all chapters (recheck)
                logger.info(f"Rechecking all chapters for {slug}")
                chapters = {}
            else:
                # Only check new chapters (after last chapter)
                last_ch_num = self.data_manager.get_last_chapter_number(slug)
                logger.info(f"Last chapter in DB: {last_ch_num}. Checking for new chapters...")
                chapters = existing_chapters.copy()
            
            new_count = 0
            for ch_title, ch_url in detail["chapter_links"].items():
                ch_num = self._extract_chapter_number(ch_title)
                
                # Skip if already have this chapter (and not checking all)
                if not check_all and ch_num in existing_chapters:
                    continue
                
                try:
                    images = self.scraper.scrape_chapter_images(ch_url)
                    
                    chapters[ch_num] = {
                        "title": ch_title,
                        "url": ch_url,
                        "images": images
                    }
                    new_count += 1
                    logger.info(f"  Added/Updated: {ch_title} ({len(images)} images)")
                    
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.error(f"Error scraping chapter {ch_title}: {e}")
            
            # Update manga data
            manga_data = {
                "title": detail["title"],
                "author": detail["author"],
                "genre": detail["genre"],
                "type": detail["type"],
                "cover": detail["cover"],
                "synopsis": detail["synopsis"],
                "source_url": url,
                "total_chapters": len(chapters),
                "chapters": chapters
            }
            
            # Paraphrase synopsis
            synopsis = self.scraper.paraphrase_synopsis(detail["synopsis"])
            
            # Save
            self.data_manager.add_or_update_manga(slug, manga_data, synopsis)
            
            logger.info(f"✓ Updated {slug}: added {new_count} new chapters")
            
        except Exception as e:
            logger.error(f"Failed to update {slug}: {e}")
            raise
    
    def _update_all_manga_chapters(self):
        """Update all registered manga with new chapters only"""
        logger.info("Updating all manga with new chapters...")
        
        index = self.data_manager.load_index()
        
        successful = 0
        skipped = 0
        failed = 0
        
        for slug, manga_info in index.items():
            url = manga_info.get("source_url")
            if not url:
                logger.warning(f"⊘ {slug} has no source_url - skipping")
                skipped += 1
                continue
            
            try:
                self._update_manga_chapters(url, check_all=False)
                successful += 1
                time.sleep(random.uniform(3, 6))
            except Exception as e:
                logger.error(f"✗ Failed to update {slug}: {e}")
                failed += 1
                time.sleep(random.uniform(2, 4))
        
        logger.info(f"\n=== Summary ===")
        logger.info(f"Total: {len(index)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Skipped: {skipped}")
        logger.info(f"Failed: {failed}")
    
    def _extract_chapter_number(self, title):
        """Extract chapter number from title like 'Chapter 1', 'Ch. 1.5', etc."""
        import re
        # Try to find decimal number (1, 1.5, 10.2, etc.)
        match = re.search(r'(\d+(?:\.\d+)?)', title)
        if match:
            num_str = match.group(1)
            # Convert to float then back to string to normalize
            try:
                num = float(num_str)
                # Format as string, but as float if needed
                return str(num)
            except:
                return num_str
        return title  # Return original title if no number found
    
    def show_help(self):
        """Show all available commands"""
        help_text = """
========================================================================
           GreedyComicHub - Manga Scraper CLI                  
========================================================================

AVAILABLE COMMANDS:

1. SCRAPE MANGA
   
   a) Scrape all manga of a specific type:
      python -m python scrape [TYPE] [--limit N]
      
      TYPE options: manga, manhua, manhwa (default: manga)
      Example: python -m python scrape manga
               python -m python scrape manga --limit 2
   
   b) Scrape a single manga from URL:
      python -m python scrape [URL]
      
      Example: python -m python scrape https://komiku.org/manga/50kg-cinderella/

2. UPDATE CHAPTERS

   a) Update all registered manga (only new chapters):
      python -m python update-chapters
      
      Only checks for chapters after the last chapter in database
      Much faster since it doesn't recheck existing chapters
   
   b) Update a single manga and recheck all chapters:
      python -m python update-chapters [URL]
      
      Example: python -m python update-chapters https://komiku.org/manga/50kg-cinderella/
      
      Rechecks ALL chapters (slower but ensures completeness)

3. UPDATE (New Chapters Only)
   
   Quick update all manga with only new chapters:
      python -m python update
      
      Same as 'update-chapters' without URL parameter
      Only adds chapters after the last known chapter

4. HELP
   
   Show this help message:
      python -m python -help
      python -m python --help

EXAMPLES:

   # Scrape all manga (with limit)
   python -m python scrape manga --limit 5

   # Scrape manga, skip first page
   python -m python scrape manhua --limit 10

NOTES:
- Image URLs are extracted, not downloaded
- Synopsis is paraphrased to casual Indonesian (gaul)
- Chapter data is stored in JSON format
- Web display fetches from data/index.json and data/{slug}.json
- Random delays added between requests to avoid detection

======================================================================
"""
        print(help_text)

def main():
    parser = argparse.ArgumentParser(
        prog='python -m python',
        description='GreedyComicHub - Manga Scraper',
        add_help=False
    )
    
    parser.add_argument('-help', '--help', action='store_true', help='Show help message')
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('arg', nargs='?', help='Argument for command')
    parser.add_argument('--limit', '-limit', type=int, help='Limit number of manga to scrape')
    
    args = parser.parse_args()
    
    hub = GreedyComicHub()
    
    if args.help or not args.command:
        hub.show_help()
        return
    
    command = args.command.lower()
    
    try:
        if command == 'scrape':
            if args.arg:
                if args.arg.startswith('http'):
                    # Single manga URL
                    hub.scrape_manga(url=args.arg, limit=args.limit)
                else:
                    # Type (manga/manhua/manhwa)
                    hub.scrape_manga(manga_type=args.arg, limit=args.limit)
            else:
                # Default: scrape all manga
                hub.scrape_manga(limit=args.limit)
        
        elif command == 'update-chapters':
            if args.arg and args.arg.startswith('http'):
                # Update specific manga
                hub.update_chapters(url=args.arg)
            else:
                # Update all manga
                hub.update_chapters()
        
        elif command == 'update':
            # Update all manga (new chapters only)
            hub.update_chapters()
        
        else:
            logger.error(f"Unknown command: {command}")
            hub.show_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\n\nScraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
