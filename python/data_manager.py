import json
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.index_file = self.data_dir / "index.json"
        self.ensure_dirs()
    
    def ensure_dirs(self):
        """Create data directories if they don't exist"""
        self.data_dir.mkdir(exist_ok=True)
    
    def load_index(self):
        """Load index.json"""
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def save_index(self, data):
        """Save index.json"""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Updated index.json with {len(data)} entries")
    
    def load_manga(self, slug):
        """Load individual manga JSON file"""
        manga_file = self.data_dir / f"{slug}.json"
        if manga_file.exists():
            with open(manga_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def save_manga(self, slug, data):
        """Save individual manga JSON file"""
        manga_file = self.data_dir / f"{slug}.json"
        with open(manga_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {slug}.json")
    
    def manga_exists(self, slug):
        """Check if manga is already in index"""
        index = self.load_index()
        return slug in index
    
    def get_manga_chapters_count(self, slug):
        """Get number of chapters for a manga"""
        manga = self.load_manga(slug)
        if manga and "chapters" in manga:
            return len(manga["chapters"])
        return 0
    
    def add_or_update_manga(self, slug, manga_data, synopsis_paraphrased):
        """Add or update manga in index and individual file"""
        index = self.load_index()
        
        # Ensure genre is a string (comma-separated)
        genre_str = manga_data["genre"]
        if isinstance(genre_str, list):
            genre_str = ", ".join(genre_str)
        
        # Add to index
        index[slug] = {
            "title": manga_data["title"],
            "author": manga_data["author"],
            "cover": manga_data["cover"],
            "sinopsis": synopsis_paraphrased,
            "genre": genre_str,
            "type": manga_data["type"],
            "source_url": manga_data["source_url"],
            "total_chapters": manga_data["total_chapters"]
        }
        
        self.save_index(index)
        
        # Save individual manga file with correct format
        chapters_data = manga_data.get("chapters", {})
        
        manga_file_data = {
            "title": manga_data["title"],
            "author": manga_data["author"],
            "genre": genre_str,
            "synopsis": synopsis_paraphrased,
            "cover": manga_data["cover"],
            "source_url": manga_data["source_url"],
            "chapters": chapters_data
        }
        
        self.save_manga(slug, manga_file_data)
    
    def get_last_chapter_number(self, slug):
        """Get last chapter number scraped for a manga"""
        manga = self.load_manga(slug)
        if manga and "chapters" in manga and manga["chapters"]:
            # Get chapter numbers and sort them
            chapter_nums = []
            for ch_key in manga["chapters"].keys():
                try:
                    # Handle formats like "1", "1.0", "1.5"
                    num = float(ch_key)
                    chapter_nums.append(num)
                except:
                    pass
            
            if chapter_nums:
                return max(chapter_nums)
        return 0
