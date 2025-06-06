import argparse
import logging
import os
import json
from urllib.parse import urlparse
from add_comic import add_comic
from update_all import update_all
from update_comic import update_comic
from update_source_url import update_source_url
from utils import read_json, write_json, add_to_queue, setup_logging, DATA_DIR
from processor import process_queue

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

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="GreedyComicHub CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Parser untuk add-comic
    add_parser = subparsers.add_parser("add-comic", help="Tambah komik baru")
    add_parser.add_argument("url", help="URL komik di komiku.org")

    # Parser untuk update-all
    update_all_parser = subparsers.add_parser("update-all", help="Update semua komik")

    # Parser untuk update
    update_parser = subparsers.add_parser("update", help="Update chapter tertentu")
    update_parser.add_argument("url", help="URL komik")
    update_parser.add_argument("--start", type=float, required=True, help="Chapter mulai")
    update_parser.add_argument("--end", type=float, required=True, help="Chapter akhir")
    update_parser.add_argument("--overwrite", action="store_true", help="Overwrite chapter")

    # Parser untuk update-source-url
    source_url_parser = subparsers.add_parser("update-source-url", help="Ganti URL lama ke URL baru")
    source_url_parser.add_argument("old_url", help="URL lama")
    source_url_parser.add_argument("new_url", help="URL baru")

    # Parser untuk update-domain
    domain_parser = subparsers.add_parser("update-domain", help="Ganti domain semua komik")
    domain_parser.add_argument("old_domain", help="Domain lama (misalnya, komiku.org)")
    domain_parser.add_argument("new_domain", help="Domain baru (misalnya, komiku.id)")

    # Parser untuk process-queue
    queue_parser = subparsers.add_parser("process-queue", help="Proses tugas di queue")
    queue_parser.add_argument("--max-tasks", type=int, default=10, help="Jumlah maksimum tugas yang diproses")
    queue_parser.add_argument("--max-processes", type=int, default=4, help="Jumlah maksimum proses paralel")

    # Parser untuk help
    help_parser = subparsers.add_parser("help", help="Tampilkan bantuan")

    args = parser.parse_args()

    valid_domains = ["komiku.org", "komiku.id"]  # Domain yang diizinkan

    if args.command == "add-comic":
        domain = urlparse(args.url).netloc
        if domain not in valid_domains:
            logging.error(f"URL {args.url} bukan dari domain yang didukung: {valid_domains}")
            print(f"Error: URL {args.url} bukan dari komiku.org atau komiku.id!")  # Tambah feedback
            return
        task = {"task": "add_comic", "url": args.url}
        add_to_queue(task)
        print(f"Berhasil menambahkan komik {args.url} ke queue!")  # Tambah feedback
    elif args.command == "update-all":
        update_all()
    elif args.command == "update":
        domain = urlparse(args.url).netloc
        if domain not in valid_domains:
            logging.error(f"URL {args.url} bukan dari domain yang didukung: {valid_domains}")
            print(f"Error: URL {args.url} bukan dari komiku.org atau komiku.id!")  # Tambah feedback
            return
        task = {
            "task": "update_comic",
            "url": args.url,
            "start": args.start,
            "end": args.end,
            "overwrite": args.overwrite
        }
        add_to_queue(task)
        print(f"Berhasil menambahkan update {args.url} ke queue!")  # Tambah feedback
    elif args.command == "update-source-url":
        update_source_url(args.old_url, args.new_url)
    elif args.command == "update-domain":
        update_domain(args.old_domain, args.new_domain)
    elif args.command == "process-queue":
        process_queue(args.max_tasks, args.max_processes)
    elif args.command == "help" or not args.command:
        parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()