from utils import read_json, write_json, git_push, read_json
from filelock import FileLock
import logging
import logging
import time

def process_queue():
    queue_file = "queue.json"
    lock = FileLock(queue_file + ".lock")
    logging.info("Memulai proses queue")

    while True:
        with lock:
            queue = read_json(queue_file) or []
            if not queue:
                logging.info("Queue kosong, proses selesai")
                break

            task = queue.pop(0)
            task["status"] = "processing"
            write_json(queue_file, queue)
            with open("queue_status.log", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Processing: {task}\n")

        try:
            logging.info(f"Sedang memproses: {task['type']} - {task['data']}")
            if task["type"] in ["comic_add", "source_update", "comic_update"]:
                git_push()  # Semua task ini butuh Git push
            task["status"] = "completed"
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            logging.error(f"Error memproses task {task['type']}: {str(e)}")

        with lock:
            queue = read_json(queue_file) or []
            queue.append(task)
            write_json(queue_file, queue)

            with open("queue_status.log", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {task['status'].capitalize()}: {task}\n")