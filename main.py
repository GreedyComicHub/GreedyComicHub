"""Main script for GreedyComicHub."""
import sys
import logging
from add_comic import add_comic
from processor import process_queue
# ... lainnya

def main():
    """Main function to handle commands."""
    logging.basicConfig(
        filename="logs/update.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8"
    )
    try:
        if len(sys.argv) < 2:
            logging.error("No command provided")
            print("Usage: python main.py <command> [args]")
            return

        command = sys.argv[1].lower()
        if command == "add" and len(sys.argv) == 3:
            add_comic(sys.argv[2])
        elif command == "process-queue":
            process_queue()
        # ... lainnya
        else:
            logging.error(f"Unknown command: {command}")
            print(f"Unknown command: {command}")
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()