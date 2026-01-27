# GreedyComicHub - CLI Guide

After moving all Python scripts to `python/` folder with relative imports, here's how to run commands:

## Setup

1. **Create config.ini in ROOT** (not in python/ folder):
```ini
[GitHub]
GitHubToken=your_personal_access_token_here
GitHubRepo=owner/repo
```

2. **Or use Environment Variable**:
```bash
set GITHUB_TOKEN=your_token_here
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Running Commands

All commands are run from the ROOT directory as a Python module:

```bash
# Help
python -m python --help

# Add new comic
python -m python add-comic https://komiku.org/manga/hell-mode-yarikomi-suki-no-gamer/

# Update all comics (latest chapters)
python -m python update-all

# Update specific chapter range
python -m python update https://komiku.org/manga/solo-leveling/ --start 1 --end 50

# Update ALL chapters for all comics (batch)
python -m python update-chapters

# List comics
python -m python list-comics --limit 10

# Update domain for all comics
python -m python update-domain komiku.org komiku.id

# Update specific comic URL
python -m python update-source-url old_url new_url
```

## Logging

- Logs go to: `logs/update.log`
- Console output shows: `[timestamp] - [LEVEL] - [message]`
- All operations are logged with `logging.info()`, `logging.error()`, etc.

## Project Structure

```
GreedyComicHub/
├── python/
│   ├── __init__.py           # Package marker
│   ├── __main__.py           # Entry point for -m python
│   ├── main.py               # CLI interface
│   ├── scraper.py            # Scraping functions
│   ├── add_comic.py          # Add new comic
│   ├── update_comic.py       # Update comic chapters
│   ├── update_chapters.py    # Batch update chapters
│   ├── update_all.py         # Update all comics
│   ├── processor.py          # Queue processor
│   ├── utils.py              # Utilities & config loader
│   ├── list_comics.py        # List comics
│   ├── push.py               # Git push
│   ├── update_source_url.py  # Update URLs
│   ├── update_source_domain.py
│   └── scraper_404.py
├── data/                     # Comic JSON files
├── logs/                     # Log files
├── public/                   # HTML output
├── config.ini               # GitHub credentials (Git-ignored)
├── requirements.txt         # Python dependencies
└── HTML/CSS/JS files        # Frontend
```

## Config Loading Strategy

The system tries to load GitHub credentials in this order:
1. **Environment variable** `GITHUB_TOKEN` (highest priority)
2. **config.ini** file at ROOT directory

If neither is available, you'll get a clear error message telling you to set one.

## Key Improvements

✅ **Fixed paths** - config.ini found from ROOT even when running from any directory  
✅ **Relative imports** - All modules use `from .module import` style  
✅ **Logging** - All operations logged for debugging  
✅ **Error handling** - Clear error messages for config issues  
✅ **Help text** - Comprehensive `--help` with examples  
✅ **No workflow changes** - Scraping, queue processing, HTML generation all preserved
