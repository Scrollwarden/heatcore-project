import multiprocessing
import random
import time

def generate_data(worker_id, task_id):
    """Simulates a time-consuming data generation process."""
    print(f"Worker {worker_id} generating data for task {task_id}...")
    time.sleep(random.uniform(0.5, 2.0))  # Simulate variable processing time
    generated_data = f"Data from task {task_id}"
    print(f"Worker {worker_id} finished task {task_id}.")
    return task_id, generated_data

def worker(queue, data_store, semaphore, worker_id):
    """Worker function that processes tasks from the queue."""
    while not queue.empty():
        try:
            with semaphore:
                task_id = queue.get_nowait()  # Get a task from the queue
                task_id, result = generate_data(worker_id, task_id)
                data_store[task_id] = result  # Store the result in the shared dictionary
        except Exception:
            break  # If the queue is empty, exit the loop

def main():
    manager = multiprocessing.Manager()
    task_queue = manager.Queue()  # Queue for tasks to process
    data_store = manager.dict()  # Dictionary to store generated data
    semaphore = multiprocessing.Semaphore(4)  # Limit to 4 concurrent workers

    # Add tasks to the queue
    for i in range(20):  # Example: 20 tasks
        task_queue.put(i)

    processes = []
    num_workers = 8  # Total number of workers to create

    # Start worker processes
    for worker_id in range(num_workers):
        p = multiprocessing.Process(target=worker, args=(task_queue, data_store, semaphore, worker_id))
        processes.append(p)
        p.start()

    # Wait for all workers to finish
    for p in processes:
        p.join()

    # Print results
    print("\nGenerated Data:")
    for task_id, data in sorted(data_store.items()):
        print(f"Task {task_id}: {data}")

if __name__ == "__main__":
    main()
