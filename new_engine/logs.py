import numpy as np
import matplotlib.pyplot as plt
import csv

class Logs:
    """Class for logs in graphic engine performence"""
    
    def __init__(self, frame_count_limit: int = 10000):
        """Class constructor

        Args:
            frame_count_limit (int, optional): amount of frame stored in logs. Defaults to 10000.
        """
        self.index = 0
        self.frame_count_limit = frame_count_limit
        self.times = np.zeros((frame_count_limit, ), dtype=np.float32)
        self.accumulated_time = np.zeros((frame_count_limit, ), dtype=np.float32)
        self.fps = np.zeros((frame_count_limit, ), dtype=np.float32)
        self.chunks_loaded = np.zeros((frame_count_limit, ), dtype=np.uint32)
        self.chunks_loading = np.zeros((frame_count_limit, ), dtype=np.uint32)

    def add_to_log(self, delta_time: float, chunks_loaded: int, chunks_loading: int):
        """Add information in logs

        Args:
            delta_time (float): the time between two frames
            chunks_loaded (int): the number of chunks being loaded
            chunks_loading (int): the number of chunks currently loading
        """
        if self.index >= self.frame_count_limit:
            print("===========================================================")
            print("!!! Not enough place in logs to add in new informations !!!")
            print("===========================================================")
            return
        self.times[self.index] = delta_time
        self.fps[self.index] = 1 / delta_time
        self.chunks_loaded[self.index] = chunks_loaded
        self.chunks_loading[self.index] = chunks_loading

        if self.index == 0:
            self.accumulated_time[self.index] = delta_time
        else:
            self.accumulated_time[self.index] = (
                self.accumulated_time[self.index - 1] + delta_time
            )

        self.index += 1

    def display_multiple_windows(self):
        """Display of performence data in mutiple windows"""
        x = self.accumulated_time[:self.index]

        metrics = [
            ("Chunks Loaded", self.chunks_loaded[:self.index], "Chunks Loaded", "orange"),
            ("FPS", self.fps[:self.index], "Frames Per Second", "green"),
            ("Chunks Loading", self.chunks_loading[:self.index], "Chunks Loading", "red"),
        ]

        for i, (title, data, ylabel, color) in enumerate(metrics):
            plt.figure(i + 1, figsize=(8, 5))
            plt.plot(x, data, label=title, color=color)
            plt.title(title)
            plt.xlabel("Time (s)")
            plt.ylabel(ylabel)
            plt.legend()
            plt.grid()
            plt.tight_layout()

        plt.show()

    def display_single_window(self):
        """Display of performence data in a single window"""
        x = self.accumulated_time[:self.index]
        fig, ax1 = plt.subplots(figsize=(10, 6))
        metrics = [
            {"data": self.fps[:self.index], "label": "FPS", "color": "green", "axis": ax1},
            {"data": self.chunks_loaded[:self.index], "label": "Chunks Loaded", "color": "orange", "axis": ax1.twinx()},
            {"data": self.chunks_loading[:self.index], "label": "Chunks Loading", "color": "red", "axis": ax1.twinx()},
        ]
        metrics[2]["axis"].spines["right"].set_position(("outward", 60))

        for metric in metrics:
            axis = metric["axis"]
            axis.plot(x, metric["data"], label=metric["label"], color=metric["color"])
            axis.set_ylabel(metric["label"], color=metric["color"])
            axis.tick_params(axis="y", labelcolor=metric["color"])
            axis.autoscale(enable=True, axis="y")

        fig.suptitle("Performance Metrics Over Time")
        ax1.set_xlabel("Time (s)")
        ax1.grid()

        fig.tight_layout()
        plt.show()

    def save(self, file_name: str):
        """Save logs to a CSV file

        Args:
            file_name (str): the file path for saving logs
        """
        with open(f"{file_name}.csv", mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Time", "FPS", "Chunks Loaded", "Chunks Loading", "Accumulated Time"])
            for i in range(self.index):
                writer.writerow([
                    self.times[i],
                    self.fps[i],
                    self.chunks_loaded[i],
                    self.chunks_loading[i],
                    self.accumulated_time[i],
                ])
        print(f"Logs saved to {file_name}.csv")

    def load(self, file_name: str):
        """Load logs from a CSV file

        Args:
            file_name (str): the file path for loading logs
        """
        with open(f"{file_name}.csv", mode="r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header
            self.index = 0  # Reset index
            for row in reader:
                if self.index >= self.frame_count_limit:
                    print("===========================================================")
                    print("!!! Not enough space in logs to load all data from file !!!")
                    print("===========================================================")
                    break
                self.times[self.index] = float(row[0])
                self.fps[self.index] = float(row[1])
                self.chunks_loaded[self.index] = int(row[2])
                self.chunks_loading[self.index] = int(row[3])
                self.accumulated_time[self.index] = float(row[4])
                self.index += 1
        print(f"Logs loaded from {file_name}.csv")

if __name__ == '__main__':
    logs = Logs()
    logs.load("new_engine/log_data")
    logs.display_single_window()