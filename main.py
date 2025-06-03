import argparse
import logging
import sys
import os
import configparser
from urllib.parse import urlparse
from utils import read_json, write_json, DATA_DIR
from add_comic import add_comic
from update_all import update_all
from update_comic import update_comic
from deploy_net import deploy_netlify

def update_path(old_url, new_url):
    """Update source_url di index.json tanpa menyatukan domain dan path."""
    logging.info(f"Update path dari {old_url} ke {new_url}")
    index_file = os.path.join(DATA_DIR, "index.json")
    index_data = read_json(index_file)

    if not index_data:
        logging.error("Index.json kosong, bro!")
        return

    old_domain = urlparse(old_url).netloc
    old_path = urlparse(old_url).path
    new_domain = urlparse(new_url).netloc
    new_path = urlparse(new_url).path

    updated = False
    for comic_id, comic_data in index_data.items():
        current_url = comic_data.get("source_url")
        if not current_url:
            continue

        current = urlparse(current_url)
        if old_domain and current.netloc == old_domain:
            new_source_url = current_url.replace(old_domain, new_domain)
            comic_data["source_url"] = new_source_url
            updated = True
            logging.info(f"Update domain {comic_id}: {current_url} -> {new_source_url}")
        if old_path and current.path == old_path:
            new_source_url = current_url.replace(old_path, new_path)
            comic_data["source_url"] = new_source_url
            updated = True
            logging.info(f"Update path {comic_id}: {current_url} -> {new_source_url}")

    if updated:
        write_json(index_file, index_data)
        logging.info("Berhasil update index.json")
        deploy_netlify()
    else:
        logging.warning("Nggak ada URL yang cocok untuk diupdate, bro!")

def main():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join("logs", "update.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )

    parser = argparse.ArgumentParser(
        description="GreedyComicHub CLI: Manage comics with scraping and Cloudinary integration.",
        epilog="Contoh: python main.py add-comic https://komiku.org/manga/magic-emperor"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    add_parser = subparsers.add_parser("add-comic", help="Tambah komik baru dari URL komiku.org")
    add_parser.add_argument("url", help="URL komik di komiku.org (contoh: https://komiku.org/manga/magic-emperor)")

    update_parser = subparsers.add_parser("update", help="Update chapter komik dari URL")
    update_parser.add_argument("url", help="URL komik di komiku.org (contoh: https://komiku.org/manga/magic-emperor)")
    update_parser.add_argument("--start", type=float, default=1.0, help="Chapter mulai (contoh: 1.0)")
    update_parser.add_argument("--end", type=float, default=float("inf"), help="Chapter akhir (contoh: 10.0)")
    update_parser.add_argument("--overwrite", action="store_true", help="Overwrite chapter lama")

    subparsers.add_parser("update-all", help="Update chapter terbaru untuk semua komik di index.json")

    path_parser = subparsers.add_parser("update-path", help="Update domain atau path di index.json")
    path_parser.add_argument("old_url", help="URL lama (contoh: https://komiku.org/manga/magic-emperor)")
    path_parser.add_argument("new_url", help="URL baru (contoh: https://komiku.id/manga/magic-emperor)")

    args = parser.parse_args()

    if args.command == "add-comic":
        add_comic(args.url)
        deploy_netlify()
    elif args.command == "update":
        update_comic(args.url, args.start, args.end, args.overwrite)
        deploy_netlify()
    elif args.command == "update-all":
        update_all()
        deploy_netlify()
    elif args.command == "update-path":
        update_path(args.old_url, args.new_url)
    else:
        parser.print_help()
        print("\nFungsi dan Contoh Perintah:")
        print("1. add-comic: Tambah komik baru dari URL, simpan metadata di index.json, dan deploy ke web.")
        print("   - Fungsi: Scraping metadata (title, synopsis, cover), simpan source_url, dan update chapter pertama.")
        print("   - Contoh: python main.py add-comic https://komiku.org/manga/magic-emperor")
        print("2. update: Update chapter komik dari URL untuk rentang chapter tertentu.")
        print("   - Fungsi: Scraping chapter baru, upload gambar ke Cloudinary, simpan di comic JSON, dan deploy ke web.")
        print("   - Contoh: python main.py update https://komiku.org/manga/magic-emperor --start 651.0 --end 652.0")
        print("3. update-all: Update chapter terbaru untuk semua komik di index.json.")
        print("   - Fungsi: Cek chapter terbaru untuk tiap komik, update jika ada, dan deploy ke web.")
        print("   - Contoh: python main.py update-all")
        print("4. update-path: Update domain atau path di source_url index.json tanpa menyatukan keduanya.")
        print("   - Fungsi: Ganti domain (misal, komiku.org ke komiku.id) atau path URL, dan deploy ke web.")
        print("   - Contoh: python main.py update-path https://komiku.org/manga/magic-emperor https://komiku.id/manga/magic-emperor")

if __name__ == "__main__":
    main()