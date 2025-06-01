"""Main script for GreedyComicHub."""
import sys
import logging
import argparse
from add_comic import add_comic
from processor import process_queue
from update_comic import update_comic, update_all_comics, change_comic_url

def print_help():
    """Display available commands and their usage."""
    print("Available commands:")
    print("- add: Add a new comic from Komiku URL.")
    print("  Example: python main.py add https://komiku.org/manga/blue-lock")
    print("- update: Update metadata or chapters for a specific comic.")
    print("  Options: --start <chapter> --end <chapter> to specify range.")
    print("  Example: python main.py update https://komiku.org/manga/magic-emperor --start 1 --end 10")
    print("- update-all: Update all comics in index.json.")
    print("  Example: python main.py update-all")
    print("- process-queue: Process tasks in queue.json.")
    print("  Example: python main.py process-queue")
    print("- change-url: Change comic URL in index.json.")
    print("  Example: python main.py change-url https://komiku.org/manga/magic-emperor https://komiku.id/manga/magic-emperor")
    print("- help: Display this help message.")
    print("  Example: python main.py help")

def main():
    """Main function to handle commands."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
        handlers=[
            logging.FileHandler("logs/update.log"),
            logging.StreamHandler()
        ]
    )
    try:
        parser = argparse.ArgumentParser(description="GreedyComicHub CLI")
        parser.add_argument("command", help="Command to execute")
        parser.add_argument("url", nargs="?", help="Comic URL for add/update")
        parser.add_argument("new_url", nargs="?", help="New URL for change-url")
        parser.add_argument("--start", type=int, help="Start chapter for update")
        parser.add_argument("--end", type=int, help="End chapter for update")
        args = parser.parse_args()

        command = args.command.lower()
        if command == "add" and args.url:
            add_comic(args.url)
        elif command == "update" and args.url:
            update_comic(args.url, start_chapter=args.start, end_chapter=args.end)
        elif command == "update-all" and not args.url:
            update_all_comics()
        elif command == "process-queue" and not args.url:
            process_queue()
        elif command == "change-url" and args.url and args.new_url:
            change_comic_url(args.url, args.new_url)
        elif command == "help":
            print_help()
        else:
            logging.error(f"Unknown command or invalid arguments: {command}")
            print(f"Unknown command or invalid arguments: {command}")
            print_help()
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()