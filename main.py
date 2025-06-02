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

    args = parser.parse_args()

    try:
        if args.command == "add-comic":
            add_comic(args.url)
            push_to_github()
        elif args.command == "update":
            update_comic(args.url, args.start, args.end, args.overwrite)
            push_to_github()
        elif args.command == "update-all":
            update_all()  # Tanpa argumen start/end/overwrite
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
        else:
            parser.print_help()
    except Exception as e:
        logging.error(f"Proses gagal: {str(e)}")
    finally:
        logging.info("=== Proses Selesai ===")

if __name__ == "__main__":
    main()