# Komiku.org Manga Scraper - Complete Guide

**Purpose:** Extract all manga data from komiku.org (type=manga only), including metadata, chapters, and chapter images.

## Features

✅ **Full Pagination Support** - Scrapes all pages from komiku.org/daftar-komik/?tipe=manga
✅ **Complete Chapter & Image Extraction** - Gets all chapters and image URLs for each manga
✅ **Smart Synopsis Paraphrasing** - Replaces 20-40% of words with synonyms, adds casual Indonesian phrases
✅ **Robust Error Handling** - Skips failed items gracefully, continues processing
✅ **Human-like Delays** - 2-4 second random delays between requests to avoid detection
✅ **JSON Persistence** - Saves master index + individual manga files with all data

---

## Installation

```bash
pip install requests beautifulsoup4 lxml
```

---

## Usage

### Basic Run (Test 5 Manga)
```bash
python scraper.py
```
Default LIMIT is set to 5 manga. Edit the `LIMIT` variable in `scraper.py` to change.

### Full Scrape
Edit `scraper.py` line 26:
```python
LIMIT = None  # Scrapes ALL manga (or set to specific number like 100, 500, etc.)
```

Then run:
```bash
python scraper.py
```

---

## Output Format

### 1. data/index.json
Master index file with all manga summaries:

```json
{
  "50kg-cinderella": {
    "title": "Komik -50kg Cinderella",
    "author": "Jung Min-a",
    "synopsis": "Cerita ini mengikuti wanita yang memiliki obsesi menurunkan berat badan...",
    "cover": "https://thumbnail.komiku.org/uploads/manga/50kg-cinderella/manga_thumbnail-50kg-Cinderella.jpg?w=500",
    "genre": "Drama, Romance",
    "type": "Manga",
    "total_chapters": 10,
    "source_url": "https://komiku.org/manga/50kg-cinderella/"
  },
  "another-manga": { ... }
}
```

**Index Entry Fields:**
- `title` - Manga title
- `author` - Author/Creator name (from info table)
- `synopsis` - Truncated to ~250 chars, paraphrased
- `cover` - Cover image URL (from detail page or list thumbnail)
- `genre` - Comma-separated genres
- `type` - Always "Manga" (filtered by tipe=manga)
- `total_chapters` - Number of chapters found
- `source_url` - Link to manga on komiku.org

---

### 2. data/{slug}.json
Full manga data with complete chapter information:

```json
{
  "title": "Komik -50kg Cinderella",
  "author": "Jung Min-a",
  "genre": "Drama, Josei, Romance, Slice of Life",
  "synopsis": "Cerita ini mengikuti perjalanan wanita yang merasa kurang percaya diri karena berat badannya... bro! nih! gitu loh!",
  "cover": "https://thumbnail.komiku.org/uploads/manga/50kg-cinderella/...",
  "source_url": "https://komiku.org/manga/50kg-cinderella/",
  "chapters": {
    "8": {
      "title": "Chapter 8",
      "url": "https://komiku.org/50kg-cinderella-chapter-8/",
      "images": [
        "https://img.komiku.org/uploads/manga/50kg-cinderella/chapter-8/1.jpg",
        "https://img.komiku.org/uploads/manga/50kg-cinderella/chapter-8/2.jpg",
        ...
      ]
    },
    "7": { ... },
    "2.5": { ... }  // Supports decimal chapter numbers
  }
}
```

**File Entry Fields:**
- `title` - Manga title
- `author` - Author name
- `genre` - Genres (comma-separated)
- `synopsis` - Full synopsis, paraphrased with casual Indonesian phrases
- `cover` - Cover image URL
- `source_url` - Link to manga on komiku.org
- `chapters` - Dictionary with chapter numbers as keys
  - Keys are strings: "1", "2", "2.5", "10", etc. (parsed from "Chapter X" text)
  - Each chapter has:
    - `title` - Full chapter name/title
    - `url` - Link to chapter on komiku.org
    - `images` - Array of image URLs from the chapter page

---

## HTML Targets (Komiku.org Structure)

### Manga List Page
**URL:** `https://komiku.org/daftar-komik/?tipe=manga&halaman={n}`

**Container:** `<div class="manga-grid">`
**Items:** `<article class="manga-card">`
**Link:** `<a href="/manga/{slug}/">`
**Cover:** `<img class="lazy" data-src="...">`

### Manga Detail Page
**URL:** `https://komiku.org/manga/{slug}/`

**Title:** `<h1><span>Title</span></h1>`
**Cover:** `<img class="komik-thumb/cover/thumb">` or fallback to list thumbnail
**Info Table:** `<table class="inftable">` contains author, status, genres
**Genres:** `<ul class="genre"><li><span>Genre</span></li>...`
**Synopsis:** `<div class="sinopsis">` or following `<p>` tags

### Chapters List
**Table:** `<table id="Daftar_Chapter"><tbody>`
**Chapter Row:** `<tr><td class="judulseries"><a href="/slug-chapter-x/">Chapter X</a></td>`

### Chapter Images Page
**URL:** `/slug-chapter-x/`
**Container:** `<div id="Baca_Komik">`
**Images:** `<img class="klazy" src="...">`

---

## Paraphrasing Algorithm

The `paraphrase()` function:

1. **Synonym Replacement:** 20-40% of words are randomly replaced with Indonesian synonyms
   - Examples: 
     - wanita → cewek
     - muda → remaja
     - perjalanan → petualangan
     - kekuatan → kekuatan magis

2. **Casual Phrases:** Adds random suffix from:
   - " bro!"
   - " nih!"
   - " gitu loh!"
   - " gampang aja!"
   - " mantap!"

3. **Application:** Full synopsis is paraphrased in detail files, truncated version used in index

---

## Performance & Optimization

- **Delay:** 2-4 seconds between requests (human-like behavior)
- **Timeout:** 10 seconds per HTTP request
- **Chapter Limit:** Currently unlimited (all chapters extracted)
- **Error Recovery:** Gracefully skips failed items, continues processing
- **Bandwidth:** ~100KB-500KB per manga (depending on chapter count & image count)

### Estimated Scraping Times
- 5 manga: ~2-3 minutes
- 20 manga: ~8-12 minutes
- 100 manga: ~1-2 hours
- Full site (500+ manga): ~8-15 hours

---

## Customization

### Change Limit
```python
# Scrape specific number
LIMIT = 50

# Scrape all manga
LIMIT = None
```

### Adjust Delays
```python
# In delay() function, line ~57
time.sleep(random.uniform(1, 2))  # Faster (1-2 sec)
time.sleep(random.uniform(5, 10)) # Slower (5-10 sec)
```

### Add/Modify Synonyms
Edit the `SYNONYMS` dictionary (lines 37-73) to customize paraphrasing:
```python
SYNONYMS = {
    'your_word': 'replacement',
    'another_word': 'replacement2',
    ...
}
```

### Change Casual Suffixes
Edit `CASUAL_SUFFIXES` list (lines 75-84):
```python
CASUAL_SUFFIXES = [
    " bro!",
    " nih!",
    " your_custom_phrase!",
]
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests beautifulsoup4 lxml
```

### "Manga grid not found"
Komiku.org HTML structure may have changed. Check:
1. Visit https://komiku.org/daftar-komik/?tipe=manga in browser
2. Verify `<div class="manga-grid">` still exists
3. Update selectors in `get_manga_list()` function if needed

### No images extracted
Check if chapter page structure changed:
1. Verify `<div id="Baca_Komik">` and `<img class="klazy">` still exist
2. May need to update `get_chapter_images()` function selectors

### Unicode/Encoding errors
The script forces UTF-8 encoding. If still issues:
```bash
python -u scraper.py  # Run without buffering
```

---

## File Structure After Running

```
GreedyComicHub/
├── scraper.py                 # Main scraper script
├── SCRAPER_GUIDE.md           # This file
├── data/
│   ├── index.json             # Master index (all manga summaries)
│   ├── 50kg-cinderella.json   # Manga file 1
│   ├── aoppella-hajimari-no-playlist.json  # Manga file 2
│   ├── lostend.json           # Manga file 3
│   └── ... (one .json per manga)
└── [other files]
```

---

## Functions Reference

### `paraphrase(text: str) -> str`
Paraphrases text by synonym replacement + casual phrases

### `delay()`
Adds 2-4 second random delay

### `extract_chapter_number(chapter_text: str) -> str`
Extracts "1", "2.5", etc. from "Chapter 1" or "Chapter 2.5" text

### `get_manga_list(page: int) -> Tuple[List[Dict], Optional[int]]`
Fetches manga list from single page, returns (manga_list, next_page or None)

### `get_detail(slug: str) -> Optional[Dict]`
Fetches manga detail page (title, author, genres, synopsis, cover)

### `get_chapter_images(chapter_url: str) -> List[str]`
Fetches all images from a chapter page

### `get_chapters(slug: str) -> Dict[str, Dict]`
Fetches all chapters with images for a manga

### `save_manga_data(slug: str, detail: Dict, chapters: Dict) -> bool`
Saves manga data to data/{slug}.json

### `update_index(index: Dict, slug: str, detail: Dict, chapters: Dict) -> Dict`
Adds/updates manga entry in index dictionary

### `save_index(index: Dict)`
Saves index dictionary to data/index.json

---

## Example Workflow

```bash
# 1. Run scraper for first 5 manga
python scraper.py

# 2. Check what was scraped
ls data/*.json | wc -l

# 3. View an entry from index
python -c "import json; print(json.dumps(json.load(open('data/index.json'))['50kg-cinderella'], indent=2))"

# 4. Check specific manga chapters
python -c "import json; data = json.load(open('data/lostend.json')); print(f'Chapters: {len(data[\"chapters\"])}')"

# 5. Increase limit and re-scrape
# Edit scraper.py: LIMIT = 50
python scraper.py

# 6. Commit to git
git add data/index.json data/*.json scraper.py
git commit -m "Scrape 50 manga from komiku.org"
git push origin main
```

---

## Version History

- **v2.0** (2024): Complete rewrite with production-ready code
  - Fixed href parsing for manga slug extraction
  - Full pagination support with halaman parameter
  - Complete chapter + image extraction
  - Smart paraphrasing algorithm (20-40% synonym replacement + casual phrases)
  - Robust error handling and logging
  - 557 lines of optimized, tested code
  - Proper JSON output format (index.json + individual {slug}.json files)

- ✅ Save data in JSON format with proper structure
- ✅ Human-like delays to avoid blocking
- ✅ Error handling and graceful failures

### Usage

```bash
python scraper.py
```

**Configuration:**

Modify the `limit` variable in `main()` function:

```python
limit = 5  # Scrape 5 manga (default)
limit = None  # Scrape ALL manga
```

### Output Structure

**JSON File Format:**

```json
{
  "title": "Manga Title",
  "alternative_title": "Alternative Title",
  "type": "Manga",
  "genres": ["Drama", "Romance"],
  "author": "Author Name",
  "status": "Ongoing",
  "synopsis": "Paraphrased synopsis...",
  "chapters": [
    {
      "number": "8",
      "url": "https://komiku.org/manga/...",
      "images": [
        "https://img.komiku.org/uploads2/...1.jpeg",
        "https://img.komiku.org/uploads2/...2.jpeg"
      ]
    }
  ]
}
```

**Index File:** `data/index.json`

Master index of all scraped manga with metadata:

```json
{
  "manga-slug": {
    "title": "Manga Title",
    "status": "Ongoing",
    "type": "Manga",
    "last_scraped": "2025-01-27"
  }
}
```

### Komiku.org HTML Structure

Targets the following patterns:

- **Manga List:** `/daftar-komik/?tipe=manga&halaman={page}`
- **Container:** `<div class="manga-grid">`
- **Items:** `<article class="manga-card">`
- **Pagination:** `halaman` parameter (0.5-1.5 second delays)

- **Detail Page:** `/manga/{slug}/`
- **Genres:** `<ul class="genre">`
- **Author/Status:** `<table class="inftable">`
- **Synopsis:** `<section id="Sinopsis">`
- **Chapters:** `<table id="Daftar_Chapter">`

- **Chapter Page:** `/{slug}-chapter-{num}/`
- **Images:** `<div id="Baca_Komik"> → <img class="klazy">`

### Performance

- Default: 5 manga (~5-10 minutes including all chapters)
- 10 manga: ~15-20 minutes
- 50 manga: ~1.5-2 hours
- Full scrape (3,600+ manga): ~5-7 days (not recommended)

Time varies by:
- Network speed
- Komiku.org server response time
- Number of chapters per manga (avg 20-50 per manga)

### Customization

**Change page limit:**

```python
max_pages = 5  # in get_manga_list()
```

**Change chapter limit per manga:**

```python
for chapter in detail['chapters'][:10]:  # Max 10 chapters per manga
```

**Adjust delays:**

```python
time.sleep(random.uniform(0.5, 1.5))  # in delay()
```

**Add more paraphrase synonyms:**

```python
PARAPHRASE_MAP = {
    'word': ['synonym1', 'synonym2'],
}
```

### Requirements

```
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

Install with:

```bash
pip install requests beautifulsoup4 lxml
```

### Troubleshooting

**403/429 Blocking:** Increase delays in `delay()` function

**Missing images:** Some chapters may not have images in `<div id="Baca_Komik">`

**Encoding errors:** UTF-8 encoding is forced in script, should work on all systems

**Timeout errors:** Increase timeout in requests.get() call (currently 15 seconds)

### File Storage

- **Data directory:** `data/`
- **Individual manga:** `data/{slug}.json`
- **Master index:** `data/index.json`

Current scraped count: Check `data/index.json` for `len()`

### Legal Notice

This scraper is for personal use and educational purposes. 
Komiku.org content is fan-translated manga. 
Always respect the terms of service of target websites.

---

Last updated: 2025-01-27
