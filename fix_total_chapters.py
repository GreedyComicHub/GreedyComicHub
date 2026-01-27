#!/usr/bin/env python3
"""Fix total_chapters in index.json by reading from individual JSON files"""

import json
import os
from pathlib import Path

DATA_DIR = Path("data")
index_file = DATA_DIR / "index.json"

# Load index.json
with open(index_file, encoding='utf-8') as f:
    index_data = json.load(f)

# For each comic in index, check if we have individual file and update total_chapters
for comic_id in index_data:
    comic_file = DATA_DIR / f"{comic_id}.json"
    
    if comic_file.exists():
        try:
            with open(comic_file, encoding='utf-8') as f:
                comic_data = json.load(f)
            
            # Count chapters from the chapters dict
            chapters = comic_data.get("chapters", {})
            total = len(chapters)
            
            # Update if different or missing
            current = index_data[comic_id].get("total_chapters", 0)
            if total != current:
                print(f"{comic_id}: {current} -> {total}")
                index_data[comic_id]["total_chapters"] = total
        except Exception as e:
            print(f"Error processing {comic_id}: {e}")

# Save updated index.json
with open(index_file, 'w', encoding='utf-8') as f:
    json.dump(index_data, f, indent=4, ensure_ascii=False)

print(f"\nUpdated {index_file}")
