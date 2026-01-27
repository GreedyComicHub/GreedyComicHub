# list_comics.py: Scrape komik dari api.komiku.org/manga/page/{page}/?tipe={tipe}, bandingkan dengan index.json
import logging
import json
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
from urllib.parse import urljoin
import sys
import io
import re
import time

# Setup logging tanpa encoding di StreamHandler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Pastiin stdout pake UTF-8 biar aman dari UnicodeEncodeError
if sys.stdout.encoding != 'UTF-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')

def get_komiku_comics(limit=None):
    """Scrape daftar komik dari semua tipe (manhwa, manga, manhua)."""
    comics = []
    seen_comic_ids = set()  # Hindari duplikat
    types = ['manhwa', 'manga', 'manhua']

    for tipe in types:
        page = 1
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"https://komiku.org/pustaka/?tipe={tipe}",
            "Connection": "keep-alive",
            "X-Requested-With": "XMLHttpRequest",
            "HX-Request": "true"
        }
        params = {"tipe": tipe}

        while True:
            try:
                base_url = f"https://api.komiku.org/manga/page/{page}/"
                logging.info(f"Scraping halaman {page} dari {base_url}?tipe={tipe}")
                response = requests.get(base_url, params=params, headers=headers, timeout=15)
                response.raise_for_status()

                # Parse HTML fragment
                soup = BeautifulSoup(response.text, 'html.parser')
                comic_elements = soup.select('div.bgei > a')
                
                if not comic_elements:
                    logging.warning(f"Tidak ada komik ditemukan di halaman {page} untuk tipe {tipe}. HTML mungkin berubah.")
                    logging.debug(f"HTML snippet: {soup.prettify()[:500]}")
                    break

                logging.info(f"Ditemukan {len(comic_elements)} komik di halaman {page} untuk tipe {tipe}")
                for comic in comic_elements:
                    parent_bge = comic.find_parent('div', class_='bge')
                    title_elem = parent_bge.select_one('div.kan h3')
                    title = title_elem.text.strip() if title_elem else 'Unknown'
                    url = urljoin("https://komiku.org/", comic.get('href', ''))
                    comic_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]

                    # Skip URL invalid atau duplikat
                    if not comic_id or 'manga' not in url.lower():
                        logging.warning(f"Skip URL tidak valid: {url}")
                        continue
                    if comic_id in seen_comic_ids:
                        logging.warning(f"Skip duplikat: {title} ({comic_id})")
                        continue
                    seen_comic_ids.add(comic_id)

                    # Ambil jumlah chapter dari chapter terbaru
                    chapter_count = 0
                    try:
                        # Cari elemen dengan teks "Terbaru"
                        latest_chapter_elems = parent_bge.select('div.new1 a')
                        for elem in latest_chapter_elems:
                            chapter_text = elem.text.strip()
                            if 'Terbaru' in chapter_text:
                                # Ekstrak nomor chapter dari teks
                                match = re.search(r'Terbaru:?\s*(?:Chapter|Ch\.|Ch)\s*([\d.]+)', chapter_text, re.IGNORECASE)
                                if match:
                                    chapter_count = float(match.group(1))
                                    logging.debug(f"Chapter terbaru untuk {title}: {chapter_text} ({chapter_count})")
                                    break
                                else:
                                    logging.warning(f"Gagal parse chapter untuk {title}: {chapter_text}")
                        if chapter_count == 0:
                            logging.warning(f"Tidak ditemukan chapter terbaru untuk {title} di API")
                    except Exception as e:
                        logging.error(f"Gagal ambil chapter dari API untuk {title} ({url}): {e}")

                    # Fallback: hit halaman komik kalau chapter 0
                    if chapter_count == 0:
                        try:
                            time.sleep(1)
                            chapter_response = requests.get(url, headers=headers, timeout=15)
                            chapter_response.raise_for_status()
                            chapter_soup = BeautifulSoup(chapter_response.text, 'html.parser')
                            # Cari daftar chapter
                            chapter_elements = chapter_soup.select('ul#chapter_list a, table.inftable td.judulseries a, div.chapter-list a')
                            if chapter_elements:
                                # Ambil chapter terbaru (biasanya pertama)
                                latest_chapter = chapter_elements[0]
                                chapter_text = latest_chapter.text.strip()
                                match = re.search(r'(?:Chapter|Ch\.|Ch)\s*([\d.]+)', chapter_text, re.IGNORECASE)
                                if match:
                                    chapter_count = float(match.group(1))
                                    logging.debug(f"Fallback berhasil untuk {title}: {chapter_text} ({chapter_count})")
                                else:
                                    logging.warning(f"Fallback gagal parse chapter untuk {title}: {chapter_text}")
                            else:
                                logging.warning(f"Tidak ditemukan chapter di halaman komik untuk {title}")
                        except Exception as e:
                            logging.error(f"Gagal ambil chapter dari halaman untuk {title} ({url}): {e}")

                    comics.append({
                        'title': title,
                        'url': url,
                        'comic_id': comic_id,
                        'chapter_count': chapter_count,
                        'tipe': tipe.capitalize()
                    })
                    logging.info(f"Berhasil tambah: {title} ({chapter_count} chapter, tipe: {tipe})")

                    # Stop kalau udah cukup (cek setelah semua tipe selesai)
                    if limit and len(comics) >= limit * 2:  # Buffer biar cukup buat filter
                        logging.info(f"Batas buffer {limit * 2} komik tercapai untuk tipe {tipe}.")
                        break

                page += 1
                if limit and len(comics) >= limit * 2:
                    break

            except Exception as e:
                logging.error(f"Error saat scraping halaman {page} untuk tipe {tipe}: {e}")
                break

    return comics

def compare_comics(limit=None):
    """Bandingkan komik dari komiku.org dengan index.json."""
    try:
        with open('data/index.json', 'r', encoding='utf-8') as f:
            local_comics = json.load(f)
        local_comic_ids = set(local_comics.keys())
    except FileNotFoundError:
        logging.warning("index.json tidak ditemukan, anggap semua komik belum ada.")
        local_comics = {}
        local_comic_ids = set()

    remote_comics = get_komiku_comics(limit)
    if not remote_comics:
        logging.warning("Tidak ada komik yang berhasil di-scrape dari komiku.org.")

    remote_comic_ids = {comic['comic_id'] for comic in remote_comics}

    # Komik yang sudah ada
    existing_comics = sorted([local_comics[cid]['title'] for cid in local_comic_ids])

    # Komik yang belum ada
    missing_comics = [
        {
            'title': comic['title'],
            'url': comic['url'],
            'chapter_count': comic['chapter_count'],
            'tipe': comic['tipe']
        }
        for comic in remote_comics if comic['comic_id'] not in local_comic_ids
    ]
    # Urutkan dari chapter terbanyak
    missing_comics = sorted(missing_comics, key=lambda x: x['chapter_count'], reverse=True)
    # Batasi sesuai limit
    if limit:
        missing_comics = missing_comics[:limit]

    return existing_comics, missing_comics

def list_comics(limit=None):
    """Tampilkan komik yang sudah ada dan belum ada."""
    existing_comics, missing_comics = compare_comics(limit)

    print("\n=== Komik yang Sudah Ada ===")
    if existing_comics:
        for title in existing_comics:
            print(f"- {title}")
    else:
        print("Belum ada komik di index.json.")

    print("\n=== Komik yang Belum Ada (Urut dari Chapter Terbanyak) ===")
    if missing_comics:
        table = [[comic['tipe'], comic['title'], comic['url'], comic['chapter_count']] for comic in missing_comics]
        print(tabulate(table, headers=['Tipe', 'Judul', 'URL', 'Jumlah Chapter'], tablefmt='grid'))
    else:
        print("Semua komik di komiku.org sudah ada di index.json.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="List komik dari komiku.org")
    parser.add_argument('--limit', type=int, help="Jumlah komik yang ditampilkan")
    args = parser.parse_args()
    list_comics(args.limit)