import multiprocessing
import time


def generate_object():
    print("Starting object generation...")
    time.sleep(4)  # Simulate the 4-frame generation time
    print("Object generated!")
    return "Generated Object"


def on_generation_complete(result):
    # Callback when the object is ready
    print(f"Result received: {result}")


if __name__ == "__main__":
    # Use a multiprocessing pool for background generation
    with multiprocessing.Pool(processes=1) as pool:
        # Start the task
        async_result = pool.apply_async(generate_object, callback=on_generation_complete)

        # Continue the game loop
        while not async_result.ready():
            print("Game running...")
            time.sleep(0.5)  # Simulate game loop

    print("Game loop finished.")