import queue
import threading

from hrafnagud.core.algorithms import PointCloudGeneration
from hrafnagud.core.driver import Driver


class Scan:

    def __init__(self):
        self.driver = Driver()
        self.is_scanning = False
        self.point_cloud_generation = PointCloudGeneration()
        self.captures_queue = queue.Queue()
        self.point_cloud_callback = None
        self.threads = []

    def start(self):
        if not self.is_scanning:
            self.is_scanning = True
            self.driver.board.connect()
            self.driver.start()
            self.threads.append(threading.Thread(target=self.capture))
            self.threads.append(threading.Thread(target=self.process))
            for t in self.threads:
                t.start()

    def join_processes(self):
        for t in self.threads:
            t.join()
        self.threads.clear()

    def stop(self):
        if self.is_scanning:
            self.is_scanning = False
            self.driver.board.disconnect()

    def capture(self):
        while self.is_scanning:
            captures = self.capture_points()
            if captures is None:
                self.stop()
                break
            self.captures_queue.put(captures)

    def capture_points(self):
        captures = self.driver.capture_data()
        return captures

    def process(self):
        while self.is_scanning:
            if not self.captures_queue.empty():
                capture = self.captures_queue.get()
                self.process_capture(capture)
                self.captures_queue.task_done()

    def process_capture(self, capture):
        if not capture:
            # TODO: raise error
            return
        scene_rotation, *capture = capture
        captures = capture[:len(capture) // 2], capture[len(capture) // 2:]
        point_cloud = self.point_cloud_generation.compute_point_cloud(
            scene_rotation,
            captures
        )
        point_cloud = point_cloud[0] + point_cloud[1]
        self.point_cloud_callback(point_cloud)
