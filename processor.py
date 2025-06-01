"""Process tasks in queue.json."""
import logging
import time
from utils import read_json, write_json, git_push
from filelock import FileLock

def process_queue():
    """Process tasks in queue.json sequentially."""
    queue_file = "queue.json"
    lock = FileLock(queue_file + ".lock")
    
    while True:
        with lock:
            queue = read_json(queue_file) or []
            if not queue:
                logging.info("Queue kosong, selesai.")
                break

            task = queue[0]
            task_type = task["type"]
            task_data = task["data"]
            task["status"] = "processing"
            write_json(queue_file, queue)
        
        try:
            logging.info(f"Sedang memproses: {task_type} - {task_data}")
            
            if task_type in ["comic_add", "comic_update", "source_update"]:
                git_push()
            else:
                logging.warning(f"Tipe task tidak dikenal: {task_type}")

            with lock:
                queue = read_json(queue_file) or []
                if queue and queue[0]["type"] == task_type and queue[0]["data"] == task_data:
                    queue[0]["status"] = "completed"
                    with open("logs/queue_status.log", "a", encoding="utf-8") as f:
                        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Completed: {task_type} - {task_data}\n")
                    queue.pop(0)
                    write_json(queue_file, queue)
                else:
                    logging.warning("Task tidak ditemukan di queue setelah proses.")

        except Exception as e:
            logging.error(f"Error processing task {task_type}: {str(e)}")
            with lock:
                queue = read_json(queue_file) or []
                if queue and queue[0]["type"] == task_type and queue[0]["data"] == task_data:
                    queue[0]["status"] = "failed"
                    write_json(queue_file, queue)
            time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(
        filename="logs/update.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    process_queue()