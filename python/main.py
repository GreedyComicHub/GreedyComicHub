# main.py: CLI untuk GreedyComicHub
import argparse
import logging
import os
import sys
import json
from .add_comic import add_comic
from .update_all import update_all
from .update_comic import update_comic
from .update_source_url import update_source_url
from .list_comics import list_comics
from .utils import read_json, write_json, setup_logging, DATA_DIR, ROOT_DIR, CONFIG_PATH
from .scraper_komiku import scrape_komiku_detail, scrape_komiku_chapter
from .batch_scrape import batch_scrape

# Setup logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def update_domain(old_domain, new_domain):
    """Update domain untuk semua komik di index.json dan file JSON komik."""
    logging.info(f"Mengganti domain dari {old_domain} ke {new_domain}...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    if not index_data:
        logging.warning("Nggak ada komik di index.json, bro!")
        return
    for comic_id in index_data:
        old_source_url = index_data[comic_id].get("source_url", "")
        if not old_source_url:
            logging.warning(f"Komik {comic_id} gak punya source_url, lewati.")
            continue
        new_source_url = old_source_url.replace(old_domain, new_domain)
        if new_source_url == old_source_url:
            logging.info(f"Komik {comic_id}: source_url {old_source_url} gak berubah, lewati.")
            continue
        index_data[comic_id]["source_url"] = new_source_url
        logging.info(f"Komik {comic_id}: Update source_url dari {old_source_url} ke {new_source_url}")
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} gak ada, lewati.")
            continue
        comic_data = read_json(comic_file)
        comic_data["source_url"] = new_source_url
        write_json(comic_file, comic_data)
        logging.info(f"Berhasil update {comic_file} dengan source_url baru: {new_source_url}")
    write_json(index_file, index_data)
    logging.info(f"Berhasil update index.json dengan domain baru.")

def update_path(old_url, new_url):
    """Update source_url untuk komik spesifik dari URL lama ke URL baru."""
    logging.info(f"Mengganti source_url dari {old_url} ke {new_url}...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    if not index_data:
        logging.warning("Nggak ada komik di index.json, bro!")
        return
    comic_id = None
    for cid in index_data:
        if index_data[cid].get("source_url", "") == old_url:
            comic_id = cid
            break
    if not comic_id:
        logging.error(f"Nggak ada komik dengan source_url {old_url} di index.json, bro!")
        return
    index_data[comic_id]["source_url"] = new_url
    logging.info(f"Komik {comic_id}: Update source_url dari {old_url} ke {new_url}")
    comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
    if not os.path.exists(comic_file):
        logging.error(f"File {comic_file} gak ada, bro!")
        return
    comic_data = read_json(comic_file)
    comic_data["source_url"] = new_url
    write_json(comic_file, comic_data)
    logging.info(f"Berhasil update {comic_file} dengan source_url baru: {new_url}")
    write_json(index_file, index_data)
    logging.info(f"Berhasil update index.json dengan source_url baru.")

def scrape_komiku_manga(slug: str):
    """Scrape komiku.org manga by slug dan simpan ke JSON."""
    logging.info(f"Scraping komiku manga: {slug}")
    detail = scrape_komiku_detail(slug)
    
    if not detail:
        logging.error(f"Failed to scrape {slug}")
        return
    
    # Save to data/{slug}.json - format matches index.json
    comic_file = os.path.join(DATA_DIR, f"{slug}.json")
    
    # Convert genre list to string if needed (for index.json compatibility)
    genre_val = detail.get("genre", "")
    if isinstance(genre_val, list):
        genre_str = ", ".join(genre_val)
    else:
        genre_str = genre_val
    
    comic_data = {
        "title": detail.get("title", "Unknown").replace("Komik ", "").strip(),
        "slug": slug,
        "author": detail.get("author", "Unknown"),
        "cover": detail.get("cover", "N/A"),
        "sinopsis": detail.get("synopsis", ""),
        "genre": genre_str,
        "type": detail.get("type", "Manga"),
        "source_url": detail.get("source_url", f"https://komiku.org/manga/{slug}/"),
        "chapters": detail.get("chapters", {}),
        "total_chapters": detail.get("total_chapters", 0)
    }
    
    write_json(comic_file, comic_data)
    logging.info(f"Saved to {comic_file}")
    
    # Update index.json with same format
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file) or {}
    index_data[slug] = {
        "title": detail.get("title", "Unknown").replace("Komik ", "").strip(),
        "author": detail.get("author", "Unknown"),
        "cover": detail.get("cover", "N/A"),
        "sinopsis": detail.get("synopsis", ""),
        "genre": genre_str,
        "type": detail.get("type", "Manga"),
        "source_url": detail.get("source_url", f"https://komiku.org/manga/{slug}/"),
        "total_chapters": detail.get("total_chapters", 0)
    }
    write_json(index_file, index_data)
    logging.info(f"Updated index.json")

def scrape_komiku_chapter_cmd(slug: str, chapter_num: str):
    """Scrape komiku.org chapter images dan simpan ke JSON."""
    logging.info(f"Scraping komiku chapter: {slug} - {chapter_num}")
    
    comic_file = os.path.join(DATA_DIR, f"{slug}.json")
    comic_data = read_json(comic_file)
    
    if not comic_data:
        logging.error(f"Comic file not found: {comic_file}")
        return
    
    # Find chapter URL from data
    if not comic_data.get("chapters"):
        logging.error(f"No chapters data for {slug}")
        return
    
    chapter_key = str(chapter_num)
    if chapter_key not in comic_data["chapters"]:
        logging.error(f"Chapter {chapter_num} not found")
        return
    
    chapter_url = comic_data["chapters"][chapter_key]["url"]
    images = scrape_komiku_chapter(chapter_url)
    
    if images:
        comic_data["chapters"][chapter_key]["images"] = images
        write_json(comic_file, comic_data)
        logging.info(f"Saved {len(images)} images for chapter {chapter_num}")
    else:
        logging.warning(f"No images found for chapter {chapter_num}")

def main():
    setup_logging()
    
    # Debug info
    logging.info(f"Working directory: {os.getcwd()}")
    logging.info(f"Root directory: {ROOT_DIR}")
    logging.info(f"Config file: {CONFIG_PATH}")
    logging.info(f"Data directory: {DATA_DIR}")
    
    parser = argparse.ArgumentParser(
        description="GreedyComicHub CLI - Scraper & Manager untuk Komik",
        epilog="""
Contoh penggunaan:
  python -m python main add-comic https://komiku.org/manga/hell-mode-yarikomi-suki-no-gamer/
  python -m python main update-all
  python -m python main update-chapters
  python -m python main list-comics --limit 10
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Command yang tersedia")
    
    # Parser untuk add-comic
    add_parser = subparsers.add_parser("add-comic", help="Tambah komik baru dari URL")
    add_parser.add_argument("url", help="URL komik di komiku.org (contoh: https://komiku.org/manga/hell-mode/)")
    
    # Parser untuk update-all
    update_all_parser = subparsers.add_parser("update-all", help="Update chapter terbaru untuk semua komik")
    
    # Parser untuk update-chapters
    update_chapters_parser = subparsers.add_parser("update-chapters", help="Update ALL chapters untuk semua komik (batch)")
    update_chapters_parser.add_argument("--start", type=float, help="Chapter mulai (opsional)")
    update_chapters_parser.add_argument("--overwrite", action="store_true", help="Overwrite chapter yang sudah ada")
    
    # Parser untuk update
    update_parser = subparsers.add_parser("update", help="Update chapter spesifik dari URL komik")
    update_parser.add_argument("url", help="URL komik")
    update_parser.add_argument("--start", type=float, required=True, help="Chapter mulai")
    update_parser.add_argument("--end", type=float, required=True, help="Chapter akhir")
    update_parser.add_argument("--overwrite", action="store_true", help="Overwrite chapter yang sudah ada")
    
    # Parser untuk update-source-url
    source_url_parser = subparsers.add_parser("update-source-url", help="Ganti source URL dari komik")
    source_url_parser.add_argument("old_url", help="URL lama")
    source_url_parser.add_argument("new_url", help="URL baru")
    
    # Parser untuk update-domain
    domain_parser = subparsers.add_parser("update-domain", help="Ganti domain untuk semua komik")
    domain_parser.add_argument("old_domain", help="Domain lama (misalnya: komiku.org)")
    domain_parser.add_argument("new_domain", help="Domain baru (misalnya: komiku.id)")
    
    # Parser untuk update-path
    path_parser = subparsers.add_parser("update-path", help="Ganti source_url komik spesifik")
    path_parser.add_argument("old_url", help="URL komik yang error")
    path_parser.add_argument("new_url", help="URL komik yang baru")
    
    # Parser untuk list-comics
    list_comics_parser = subparsers.add_parser("list-comics", help="List komik (sudah ada vs belum ada)")
    list_comics_parser.add_argument('--limit', type=int, help="Batasi jumlah komik (contoh: --limit 5)")
    
    # Parser untuk scrape-komiku-manga
    scrape_manga_parser = subparsers.add_parser("scrape-komiku", help="Scrape komiku.org manga by slug")
    scrape_manga_parser.add_argument("slug", help="Manga slug (e.g., lostend)")
    
    # Parser untuk scrape-komiku-chapter
    scrape_chapter_parser = subparsers.add_parser("scrape-komiku-chapter", help="Scrape komiku chapter images")
    scrape_chapter_parser.add_argument("slug", help="Manga slug")
    scrape_chapter_parser.add_argument("chapter", help="Chapter number (e.g., 1 atau 1.5)")
    
    # Parser untuk batch-scrape
    batch_scrape_parser = subparsers.add_parser("batch-scrape", help="Batch scrape semua manga dari komiku.org")
    batch_scrape_parser.add_argument("--resume", help="Resume dari manga slug tertentu (opsional)")
    batch_scrape_parser.add_argument("--genre", help="Filter by genre: action, horror, romance, etc (opsional)")
    batch_scrape_parser.add_argument("--limit", type=int, help="Limit jumlah manga yang di-scrape (opsional)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        logging.info(f"Executing command: {args.command}")
        if args.command == "add-comic":
            add_comic(args.url)
        elif args.command == "update-all":
            update_all()
        elif args.command == "update":
            update_comic(args.url, args.start, args.end, args.overwrite)
        elif args.command == "update-source-url":
            update_source_url(args.old_url, args.new_url)
        elif args.command == "update-domain":
            update_domain(args.old_domain, args.new_domain)
        elif args.command == "update-path":
            update_path(args.old_url, args.new_url)
        elif args.command == "list-comics":
            list_comics(args.limit)
        elif args.command == "update-chapters":
            update_all_chapters(args.start, args.overwrite)
        elif args.command == "scrape-komiku":
            scrape_komiku_manga(args.slug)
        elif args.command == "scrape-komiku-chapter":
            scrape_komiku_chapter_cmd(args.slug, args.chapter)
        elif args.command == "batch-scrape":
            batch_scrape(genre=args.genre, resume_from=args.resume, limit=args.limit)
        logging.info(f"Command '{args.command}' completed successfully")
    except Exception as e:
        logging.error(f"Error executing '{args.command}': {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()