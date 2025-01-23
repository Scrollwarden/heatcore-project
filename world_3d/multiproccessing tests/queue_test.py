import multiprocessing
import time

def update():
    # Simulate a heavy computation
    print("Updating object in the background...")
    time.sleep(2)  # Simulate time-consuming task
    return "Updated Object"

def run():
    object = None
    update_process = None
    result_queue = multiprocessing.Queue()
    last_time = time.time()

    while True:
        if condition():
            if update_process is None or not update_process.is_alive():
                # Start the update process
                update_process = multiprocessing.Process(target=update_worker, args=(result_queue,))
                update_process.start()

        # Check if the update process has finished and retrieve the result
        if not result_queue.empty():
            object = result_queue.get_no_wait()
            print(f"Object updated: {object}")

        # Render loop
        render()
        end_time = time.time()
        print(f"Took: {end_time - last_time:.3f}s")
        last_time = end_time

def update_worker(queue):
    updated_object = update()
    queue.put(updated_object)

def render():
    print("Rendering frame...")
    time.sleep(0.1)  # Simulate rendering time

def condition():
    # Simulate a condition to trigger the update
    return True  # Replace with actual game logic

if __name__ == "__main__":
    run()
