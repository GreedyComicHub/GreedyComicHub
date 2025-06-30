# clean_chapters.py: Rapihin tulisan chapter di semua data/<comic>.json
import os
import json
from utils import read_json, write_json, DATA_DIR

def clean_chapter_numbers():
    logging.info("Mulai rapihin tulisan chapter di semua file JSON...")
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json') and filename != 'index.json' and filename != 'updates.json':
            comic_file = os.path.join(DATA_DIR, filename)
            comic_data = read_json(comic_file)
            if 'chapters' in comic_data:
                updated_chapters = {}
                for chapter_num, chapter_info in comic_data['chapters'].items():
                    try:
                        num = float(chapter_num)
                        display_num = int(num) if num.is_integer() else num
                        updated_chapters[str(display_num)] = chapter_info
                    except ValueError:
                        logging.warning(f"Ga bisa parse chapter {chapter_num} di {filename}, lewati.")
                        updated_chapters[chapter_num] = chapter_info
                comic_data['chapters'] = updated_chapters
                comic_data['total_chapters'] = len(updated_chapters)
                write_json(comic_file, comic_data)
                logging.info(f"Berhasil rapihin chapter di {filename}")
            else:
                logging.info(f"Ga ada chapters di {filename}, lewati.")

if __name__ == "__main__":
    from utils import setup_logging
    setup_logging()
    clean_chapter_numbers()