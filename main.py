import argparse
import logging
from add_comic import add_comic
from update_comic import update_comic
from update_all import update_all
from update_source_domain import update_source_domain
from utils import setup_logging, push_to_git

try:
    from update_source_url import update_source_url
except ImportError:
    update_source_url = None
    logging.warning("update_source_url.py not found.")
try:
    from processor import process_queue
except ImportError:
    process_queue = None
    logging.warning("processor.py not found.")

setup_logging()

def print_help_menu():
    print("\n=== GreedyComicHub Commands ===")
    commands = [
        {"name": "add-comic", "desc": "Nambah komik.", "example": "python main.py add-comic https://komiku.org/manga/komik-one-piece-indo"},
        {"name": "update", "desc": "Update chapter.", "example": "python main.py update https://komiku.org/manga/komik-one-piece-indo --start 1 --end 2"},
        {"name": "update-all", "desc": "Update semua komik.", "example": "python main.py update-all"},
        {"name": "update-source-domain", "desc": "Ganti domain.", "example": "python main.py update-source-domain thumbnail.komiku.org thumbnail.komiku.id"},
        {"name": "update-source-url", "desc": "Ganti URL.", "example": "python main.py update-source-url https://komiku.org/manga/magic-emperor https://komiku.org/manga/magicemperor"},
        {"name": "process-queue", "desc": "Proses queue.", "example": "python main.py process-queue --max-tasks 5"},
        {"name": "help", "desc": "Menu ini.", "example": "python main.py help"}
    ]
    for cmd in commands:
        print(f"Command: {cmd['name']}\nFungsi: {cmd['desc']}\nContoh: {cmd['example']}\n")
    print("Log di logs/update.log.")

def main():
    logging.info("=== Mulai ===")
    parser = argparse.ArgumentParser(description="GreedyComicHub Scraper")
    subparsers = parser.add_subparsers(dest="command")

    parser_add = subparsers.add_parser("add-comic")
    parser_add.add_argument("url")

    parser_update = subparsers.add_parser("update")
    parser_update.add_argument("url")
    parser_update.add_argument("--start", type=float, default=1.0)
    parser_update.add_argument("--end", type=float, default=1.0)
    parser_update.add_argument("--overwrite", action="store_true")

    subparsers.add_parser("update-all")

    parser_domain = subparsers.add_parser("update-source-domain")
    parser_domain.add_argument("old_domain")
    parser_domain.add_argument("new_domain")
    parser_domain.add_argument("--path-prefix", nargs=2, metavar=("OLD_PATH", "NEW_PATH"))

    if update_source_url:
        parser_url = subparsers.add_parser("update-source-url")
        parser_url.add_argument("old_url")
        parser_url.add_argument("new_url")

    if process_queue:
        parser_queue = subparsers.add_parser("process-queue")
        parser_queue.add_argument("--max-tasks", type=int, default=6)

    subparsers.add_parser("help")

    args = parser.parse_args()

    try:
        if args.command == "add-comic":
            add_comic(args.url)
            push_to_git()
        elif args.command == "update":
            update_comic(args.url, args.start, args.end, args.overwrite)
            push_to_git()
        elif args.command == "update-all":
            update_all()
            push_to_git()
        elif args.command == "update-source-domain":
            update_source_domain(args.old_domain, args.new_domain, *args.path_prefix if args.path_prefix else (None, None))
            push_to_git()
        elif args.command == "update-source-url" and update_source_url:
            update_source_url(args.old_url, args.new_url)
            push_to_git()
        elif args.command == "process-queue" and process_queue:
            process_queue(args.max_tasks)
            push_to_git()
        elif args.command == "help":
            print_help_menu()
        else:
            parser.print_help()
    except Exception as e:
        logging.error(f"Gagal: {e}")
    finally:
        logging.info("=== Selesai ===")

if __name__ == "__main__":
    main()