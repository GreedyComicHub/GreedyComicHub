import logging
import time
import os
from add_comic import add_comic
from update_comic import update_comic
from utils import read_json, write_json, QUEUE_FILE, LOG_DIR

def process_queue(max_tasks=10):
    logging.info(f"Memproses queue (max {max_tasks} tugas)...")
    queue = read_json(QUEUE_FILE)
    if not queue:
        logging.info("Queue kosong.")
        return
    processed = 0
    new_queue = []
    for task in queue:
        if processed >= max_tasks:
            new_queue.append(task)
            continue
        try:
            log_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - Processing task: {task}"
            with open(os.path.join(LOG_DIR, "queue_status.log"), "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
            logging.info(log_entry)
            if task["task"] == "add_comic":
                add_comic(task["url"])
            elif task["task"] == "update_comic":
                update_comic(
                    task["url"],
                    task.get("start", 1.0),
                    task.get("end", 1.0),
                    task.get("overwrite", False)
                )
            processed += 1
        except Exception as e:
            error_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR - Failed task: {task} ({str(e)})"
            with open(os.path.join(LOG_DIR, "queue_status.log"), "a", encoding="utf-8") as f:
                f.write(error_entry + "\n")
            logging.error(error_entry)
            new_queue.append(task)
    write_json(QUEUE_FILE, new_queue)
    final_log = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - Selesai memproses {processed} tugas, {len(new_queue)} tugas tersisa"
    with open(os.path.join(LOG_DIR, "queue_status.log"), "a", encoding="utf-8") as f:
        f.write(final_log + "\n")
    logging.info(final_log)