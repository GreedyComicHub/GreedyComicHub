import logging
import time
import os
from multiprocessing import Pool
from add_comic import add_comic
from update_comic import update_comic
from utils import read_json, write_json, QUEUE_FILE, LOG_DIR, setup_logging, push_to_github

def process_task(task):
    """Proses satu tugas dari queue."""
    try:
        log_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - [CHECKPOINT] Processing task: {task}"
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
        logging.info(f"[CHECKPOINT] Selesai proses tugas: {task}")
        return True
    except Exception as e:
        error_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR - [CHECKPOINT] Failed task: {task} ({str(e)})"
        with open(os.path.join(LOG_DIR, "queue_status.log"), "a", encoding="utf-8") as f:
            f.write(error_entry + "\n")
        logging.error(error_entry)
        return False, task

def process_queue(max_tasks=10, max_processes=4):
    """Proses queue dengan multiprocessing, batasi max_processes."""
    logging.info(f"Memproses queue (max {max_tasks} tugas, max {max_processes} proses)...")
    queue = read_json(QUEUE_FILE)
    if not queue:
        logging.info("Queue kosong.")
        return
    
    processed = 0
    new_queue = []
    
    tasks_to_process = queue[:max_tasks]
    remaining_tasks = queue[max_tasks:]
    
    with Pool(processes=max_processes) as pool:
        results = pool.map(process_task, tasks_to_process)
    
    for task, result in zip(tasks_to_process, results):
        if result is True:
            processed += 1
        else:
            new_queue.append(result[1])
    
    new_queue.extend(remaining_tasks)
    
    write_json(QUEUE_FILE, new_queue)
    
    final_log = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - INFO - [CHECKPOINT] Selesai memproses {processed} tugas, {len(new_queue)} tugas tersisa"
    with open(os.path.join(LOG_DIR, "queue_status.log"), "a", encoding="utf-8") as f:
        f.write(final_log + "\n")
    logging.info(final_log)
    
    # Push perubahan ke GitHub
    push_to_github()

if __name__ == "__main__":
    setup_logging()
    process_queue()