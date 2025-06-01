import sys
from add_comic import add_comic
from update_comic import update_comic
from update_all import update_all_comics
from update_source_domain import update_source_domain
from update_source_url import update_source_url
from processor import process_queue
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/update.log"),
        logging.StreamHandler()
    ]
)

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command> [args]")
        print("Commands: add, update, update-all, update-source-domain, update-source-url, process-queue")
        return

    command = sys.argv[1]
    try:
        if command == "add":
            if len(sys.argv) != 3:
                print("Usage: python main.py add <comic_url>")
                return
            add_comic(sys.argv[2])
        elif command == "update":
            if len(sys.argv) != 3:
                print("Usage: python main.py update <comic_url>")
                return
            update_comic(sys.argv[2])
        elif command == "update-all":
            update_all_comics()
        elif command == "update-source-domain":
            if len(sys.argv) != 4 or sys.argv[3] != "ke":
                print("Usage: python main.py update-source-domain <old_domain> ke <new_domain>")
                return
            update_source_domain(sys.argv[2], sys.argv[4])
        elif command == "update-source-url":
            if len(sys.argv) != 4 or sys.argv[3] != "ke":
                print("Usage: python main.py update-source-url <old_url> ke <new_url>")
                return
            update_source_url(sys.argv[2], sys.argv[4])
        elif command == "process-queue":
            process_queue()
        else:
            print(f"Unknown command: {command}")
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()