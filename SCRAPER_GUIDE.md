## Komiku.org Manga Scraper

Complete Python script to scrape manga data from komiku.org (type: manga only).

### Features

- ✅ Scrape manga list with full pagination support
- ✅ Extract manga details (title, author, genres, status, synopsis)
- ✅ Scrape all chapters with image URLs
- ✅ Paraphrase synopsis using synonym replacement
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
