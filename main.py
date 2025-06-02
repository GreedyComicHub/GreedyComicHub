import argparse
import logging
from add_comic import add_comic
from update_comic import update_comic
from update_all import update_all
from update_source_domain import update_source_domain
from update_source_url import update_source_url
from processor import process_queue
from utils import setup_logging, push_to_github

# Setup logging
setup_logging()

def print_help_menu():
    """Tampilkan daftar command, fungsi, dan contoh penggunaan."""
    print("\n=== GreedyComicHub Commands ===")
    print("Berikut daftar command yang bisa kamu pake, bro!\n")
    
    commands = [
        {
            "name": "add-comic",
            "desc": "Nambah komik baru dari URL, simpen detail (judul, author, sinopsis, dll.) ke JSON.",
            "example": "python main.py add-comic https://komiku.org/manga/komik-one-piece-indo"
        },
        {
            "name": "update",
            "desc": "Update chapter komik dari URL, scrape gambar, upload ke Cloudinary, simpen ke JSON.",
            "example": "python main.py update https://komiku.org/manga/komik-one-piece-indo --start 1 --end 2"
        },
        {
            "name": "update-all",
            "desc": "Cek semua komik di index.json, tambah chapter baru otomatis kalau ada update.",
            "example": "python main.py update-all"
        },
        {
            "name": "update-source-domain",
            "desc": "Ganti domain di semua JSON (cover & chapter), misal komiku.org ke komiku.id.",
            "example": "python main.py update-source-domain komiku.org komiku.id"
        },
        {
            "name": "update-source-url",
            "desc": "Ganti URL spesifik di semua JSON (cover & chapter).",
            "example": "python main.py update-source-url https://komiku.org/old.jpg https://komiku.id/new.jpg"
        },
        {
            "name": "process-queue",
            "desc": "Proses task di queue.json (add/update comic) secara berurutan.",
            "example": "python main.py process-queue --max-tasks 5"
        },
        {
            "name": "help",
            "desc": "Nampilin daftar command ini, fungsi, sama contohnya.",
            "example": "python main.py help"
        }
    ]
    
    for cmd in commands:
        print(f"Command: {cmd['name']}")
        print(f"Fungsi: {cmd['desc']}")
        print(f"Contoh: {cmd['example']}\n")
    
    print("=== Tips ===")
    print("- Semua command otomatis push ke GitHub, pastiin config.ini punya token valid.")
    print("- Log disimpen di logs/update.log, cek kalau ada error.")
    print("- Mau nambah komik barengan? Pake process-queue biar nggak tabrakan, bro!")
    print("==============\n")

def main():
    logging.info("=== Mulai Proses GreedyComicHub ===")
    parser = argparse.ArgumentParser(description="GreedyComicHub Scraper")
    subparsers = parser.add_subparsers(dest="command")

    # Add comic
    parser_add = subparsers.add_parser("add-comic", help="Add new comic details")
    parser_add.add_argument("url", help="Comic URL")

    # Update comic
    parser_update = subparsers.add_parser("update", help="Update comic chapters")
    parser_update.add_argument("url", help="Comic URL")
    parser_update.add_argument("--start", type=float, default=1.0, help="Start chapter")
    parser_update.add_argument("--end", type=float, default=1.0, help="End chapter")
    parser_update.add_argument("--overwrite", action="store_true", help="Overwrite existing chapters")

    # Update all comics
    parser_update_all = subparsers.add_parser("update-all", help="Update all comics with new chapters automatically")

    # Update source domain
    parser_domain = subparsers.add_parser("update-source-domain", help="Update source domain")
    parser_domain.add_argument("old_domain", help="Old domain (e.g., komiku.org)")
    parser_domain.add_argument("new_domain", help="New domain (e.g., komiku.id)")

    # Update source URL
    parser_url = subparsers.add_parser("update-source-url", help="Update source URL")
    parser_url.add_argument("old_url", help="Old URL")
    parser_url.add_argument("new_url", help="New URL")

    # Process queue
    parser_queue = subparsers.add_parser("process-queue", help="Process tasks in queue")
    parser_queue.add_argument("--max-tasks", type=int, default=10, help="Max tasks to process")

    # Help menu
    parser_help = subparsers.add_parser("help", help="Show all commands and examples")

    args = parser.parse_args()

    try:
        if args.command == "add-comic":
            add_comic(args.url)
            push_to_github()
        elif args.command == "update":
            update_comic(args.url, args.start, args.end, args.overwrite)
            push_to_github()
        elif args.command == "update-all":
            update_all()
            push_to_github()
        elif args.command == "update-source-domain":
            update_source_domain(args.old_domain, args.new_domain)
            push_to_github()
        elif args.command == "update-source-url":
            update_source_url(args.old_url, args.new_url)
            push_to_github()
        elif args.command == "process-queue":
            process_queue(args.max_tasks)
            push_to_github()
        elif args.command == "help":
            print_help_menu()
        else:
            parser.print_help()
    except Exception as e:
        logging.error(f"Proses gagal: {str(e)}")
    finally:
        logging.info("=== Proses Selesai ===")

if __name__ == "__main__":
    main()