import argparse
import logging
import os
from urllib.parse import urlparse
from add_comic import add_comic
from update_all import update_all
from update_comic import update_comic
from update_source_url import update_source_url
from utils import read_json, write_json, add_to_queue, setup_logging, DATA_DIR
from processor import process_queue

def update_domain(old_domain, new_domain):
    logging.info(f"Ganti domain dari {old_domain} ke {new_domain}...")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)
    if not index_data:
        logging.warning("index.json kosong, bro!")
        return
    for comic_id in index_data:
        old_source_url = index_data[comic_id].get("source_url", "")
        if not old_source_url:
            logging.warning(f"Komik {comic_id} nggak punya source_url, skip.")
            continue
        new_source_url = old_source_url.replace(old_domain, new_domain)
        if new_source_url == old_source_url:
            logging.info(f"Komik {comic_id}: source_url {old_source_url} nggak berubah, skip.")
            continue
        index_data[comic_id]["source_url"] = new_source_url
        logging.info(f"Komik {comic_id}: Update source_url dari {old_source_url} ke {new_source_url}")
        comic_file = os.path.join(DATA_DIR, f"{comic_id}.json")
        if not os.path.exists(comic_file):
            logging.error(f"File {comic_file} nggak ada, skip.")
            continue
        comic_data = read_json(comic_file)
        comic_data["source_url"] = new_source_url
        write_json(comic_file, comic_data)
        logging.info(f"Update {comic_file} dengan source_url baru: {new_source_url}")
    write_json(index_file, index_data)
    logging.info(f"Update index.json dengan domain baru.")

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="GreedyComicHub CLI")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add-comic", help="Tambah komik baru")
    add_parser.add_argument("url", help="URL komik di komiku.org")

    update_all_parser = subparsers.add_parser("update-all", help="Update semua komik")

    update_parser = subparsers.add_parser("update", help="Update chapter tertentu")
    update_parser.add_argument("url", help="URL komik")
    update_parser.add_argument("--start", type=float, required=True, help="Chapter mulai")
    update_parser.add_argument("--end", type=float, required=True, help="Chapter akhir")
    update_parser.add_argument("--overwrite", action="store_true", help="Overwrite chapter")

    source_url_parser = subparsers.add_parser("update-source-url", help="Ganti URL lama ke URL baru")
    source_url_parser.add_argument("old_url", help="URL lama")
    source_url_parser.add_argument("new_url", help="URL baru")

    domain_parser = subparsers.add_parser("update-domain", help="Ganti domain semua komik")
    domain_parser.add_argument("old_domain", help="Domain lama (misal, komiku.org)")
    domain_parser.add_argument("new_domain", help="Domain baru (misal, komiku.id)")

    queue_parser = subparsers.add_parser("process-queue", help="Proses tugas di queue")
    queue_parser.add_argument("--max-tasks", type=int, default=10, help="Maks tugas diproses")
    queue_parser.add_argument("--max-processes", type=int, default=4, help="Maks proses paralel")

    check_queue_parser = subparsers.add_parser("check-queue", help="Cek isi queue")

    help_parser = subparsers.add_parser("help", help="Tampilkan bantuan")

    args = parser.parse_args()

    valid_domains = ["komiku.org", "komiku.id"]

    if args.command == "add-comic":
        domain = urlparse(args.url).netloc
        if domain not in valid_domains:
            logging.error(f"Error: URL {args.url} bukan dari {valid_domains}")
            print(f"Error: URL {args.url} bukan dari komiku.org atau komiku.id!")
            return
        task = {"task": "add_comic", "url": args.url}
        add_to_queue(task)
        print(f"Berhasil menambahkan komik {args.url} ke queue! Jalankan 'process-queue'.")
    elif args.command == "update-all":
        update_all()
    elif args.command == "update":
        domain = urlparse(args.url).netloc
        if domain not in valid_domains:
            logging.error(f"Error: URL {args.url} bukan dari {valid_domains}")
            print(f"Error: URL {args.url} bukan dari komiku.org atau komiku.id!")
            return
        task = {
            "task": "update_comic",
            "url": args.url,
            "start": args.start,
            "end": args.end,
            "overwrite": args.overwrite
        }
        add_to_queue(task)
        print(f"Berhasil menambahkan update {args.url} ke queue! Jalankan 'process-queue'.")
    elif args.command == "update-source-url":
        update_source_url(args.old_url, args.new_url)
    elif args.command == "update-domain":
        update_domain(args.old_domain, new_domain)
    elif args.command == "process-queue":
        process_queue(args.max_tasks, args.max_processes)
    elif args.command == "check-queue":
        queue = read_json(os.path.join(DATA_DIR, "queue.json"))
        if not queue:
            print("Queue kosong, bro!")
        else:
            print(f"Jumlah tugas di queue: {len(queue)}")
            for i, task in enumerate(queue, 1):
                print(f"{i}. {task}")
    elif args.command == "help" or not args.command:
        parser.print_help()

if __name__ == "__main__":
    main()