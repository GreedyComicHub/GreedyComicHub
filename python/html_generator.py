"""
html_generator.py: Generate HTML pages dari scraped manga data
Sesuaikan dengan UI GreedyComicHub
"""
import json
import os
from pathlib import Path
from typing import Dict, List

def get_data_dir():
    """Get data directory path."""
    root = Path(__file__).parent.parent
    return root / "data"

def generate_manga_page(manga_data: Dict) -> str:
    """Generate HTML page untuk manga detail."""
    slug = manga_data.get("slug", "unknown")
    title = manga_data.get("title", "Unknown")
    cover_url = manga_data.get("cover_url", "")
    sinopsis = manga_data.get("sinopsis", "")
    genres = manga_data.get("genres", [])
    chapters = manga_data.get("chapters", [])
    
    genres_html = " • ".join(genres) if genres else "N/A"
    
    # Generate chapter list
    chapters_html = ""
    for ch in chapters:
        if isinstance(ch, dict):
            ch_num = ch.get("number", "Unknown")
            ch_url = ch.get("url", "#")
            ch_date = ch.get("date", "")
        else:
            # chapters might be list of strings
            ch_num = str(ch)
            ch_url = "#"
            ch_date = ""
        
        chapters_html += f'''
        <div class="chapter-item">
            <a href="chapter.html?url={ch_url}" class="chapter-link">
                <span class="chapter-num">{ch_num}</span>
                <span class="chapter-date">{ch_date}</span>
            </a>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - GreedyComicHub</title>
    <meta name="description" content="{sinopsis[:150]}...">
    <link rel="stylesheet" href="style.css?v=2">
</head>
<body>
    <header class="main-header">
        <a href="index.html" class="logo">Greedy<span>Comic</span>Hub</a>
        <button id="theme-toggle" aria-label="Toggle theme" title="Toggle dark/light mode">🌙</button>
    </header>
    
    <main class="manga-detail">
        <div class="manga-header">
            <div class="manga-cover">
                <img src="{cover_url}" alt="{title}" loading="lazy">
            </div>
            <div class="manga-info">
                <h1>{title}</h1>
                <p class="genres">{genres_html}</p>
                <p class="sinopsis">{sinopsis}</p>
                <p class="chapter-count">Total Chapters: {len(chapters)}</p>
            </div>
        </div>
        
        <div class="chapters-section">
            <h2>Chapters ({len(chapters)})</h2>
            <div class="chapters-list">
                {chapters_html}
            </div>
        </div>
    </main>
    
    <footer>
        <p>&copy; 2025 GreedyComicHub. All rights reserved.</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
    '''
    return html

def generate_chapter_page(chapter_url: str, images: List[str]) -> str:
    """Generate HTML page untuk chapter dengan images."""
    images_html = ""
    for i, img_url in enumerate(images, 1):
        images_html += f'<img src="{img_url}" alt="Page {i}" loading="lazy" class="chapter-image">\n'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chapter - GreedyComicHub</title>
    <link rel="stylesheet" href="style.css?v=2">
</head>
<body>
    <header class="main-header">
        <a href="index.html" class="logo">Greedy<span>Comic</span>Hub</a>
        <button id="theme-toggle" aria-label="Toggle theme" title="Toggle dark/light mode">🌙</button>
    </header>
    
    <main class="chapter-viewer">
        <div class="chapter-images">
            {images_html}
        </div>
    </main>
    
    <footer>
        <p>&copy; 2025 GreedyComicHub. All rights reserved.</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
    '''
    return html

def generate_list_page(all_manga: List[Dict]) -> str:
    """Generate HTML page untuk list semua manga."""
    manga_items = ""
    for manga in all_manga:
        slug = manga.get("slug", "")
        title = manga.get("title", "Unknown")
        cover_url = manga.get("cover_url", "")
        
        manga_items += f'''
        <div class="manga-card">
            <a href="manga.html?slug={slug}">
                <div class="manga-cover">
                    <img src="{cover_url}" alt="{title}" loading="lazy">
                </div>
                <h3>{title}</h3>
            </a>
        </div>
        '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Manga - GreedyComicHub</title>
    <link rel="stylesheet" href="style.css?v=2">
</head>
<body>
    <header class="main-header">
        <a href="index.html" class="logo">Greedy<span>Comic</span>Hub</a>
        <input type="text" id="search-bar" class="search-bar" placeholder="Search comics...">
        <button id="theme-toggle" aria-label="Toggle theme" title="Toggle dark/light mode">🌙</button>
    </header>
    
    <main class="manga-list-page">
        <h1>All Manga</h1>
        <div class="manga-grid">
            {manga_items}
        </div>
    </main>
    
    <footer>
        <p>&copy; 2025 GreedyComicHub. All rights reserved.</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
    '''
    return html

def main():
    """Generate all HTML pages dari data."""
    data_dir = get_data_dir()
    root_dir = data_dir.parent
    
    # Load index.json
    index_file = data_dir / "index.json"
    if not index_file.exists():
        print("❌ index.json not found")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    # Index format is dict keyed by slug, convert to list
    if isinstance(index_data, dict):
        all_manga = [
            {
                "slug": slug,
                "title": data.get("title", slug),
                "cover_url": data.get("cover", ""),
                "sinopsis": data.get("synopsis", "")
            }
            for slug, data in index_data.items()
        ]
    else:
        all_manga = index_data.get("comics", [])
    
    print(f"📖 Loaded {len(all_manga)} manga from index")
    
    # Generate list page
    list_page_html = generate_list_page(all_manga)
    list_page_file = root_dir / "list_comics.html"
    with open(list_page_file, 'w', encoding='utf-8') as f:
        f.write(list_page_html)
    print(f"✓ Generated list_comics.html")
    
    # Generate individual manga pages
    for manga in all_manga:
        slug = manga.get("slug", "")
        if not slug:
            continue
        
        # Check if full data exists
        manga_file = data_dir / f"{slug}.json"
        if not manga_file.exists():
            print(f"⚠ Skipping {slug} - data not found")
            continue
        
        with open(manga_file, 'r', encoding='utf-8') as f:
            manga_data = json.load(f)
        
        # Generate manga page
        page_html = generate_manga_page(manga_data)
        page_file = root_dir / f"manga-{slug}.html"
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(page_html)
        print(f"✓ Generated manga-{slug}.html")
    
    print(f"\n✅ HTML generation complete!")

if __name__ == "__main__":
    main()
