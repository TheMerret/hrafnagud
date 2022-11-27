import queue
import threading

from hrafnagud.core.algorithms import ImageCapture, PointCloudGeneration
from hrafnagud.core.driver import Driver


class Scan:

    def __init__(self):
        self.driver = Driver()
        self.is_scanning = False
        self.image_capture = ImageCapture(self.driver)
        self.point_cloud_generation = PointCloudGeneration()
        self.captures_queue = queue.Queue()
        self.scene_rotation = 0
        self.point_cloud_callback = None
        self.scene_rotation_step = 1

    def start(self):
        if not self.is_scanning:
            self.is_scanning = True
            threading.Thread(target=self.capture).start()
            threading.Thread(target=self.process).start()

    def stop(self):
        self.is_scanning = False
        self.driver.board.disconnect()

    def capture(self):
        while self.is_scanning:
            captures = self.capture_points()
            self.captures_queue.put(captures)

    def capture_points(self):
        captures = self.image_capture.capture_lasers()
        return captures

    def process(self):
        while self.is_scanning:
            if self.scene_rotation > 360:
                break
            if not self.captures_queue.empty():
                capture = self.captures_queue.get()
                self.process_capture(capture)
                self.captures_queue.task_done()

            self.driver.board.motor_move(self.scene_rotation_step)
            self.scene_rotation += self.scene_rotation_step

    def process_capture(self, capture):
        point_cloud = self.point_cloud_generation.compute_point_cloud(
            self.scene_rotation,
            capture
        )
        point_cloud = point_cloud[0] + point_cloud[1]
        self.point_cloud_callback(point_cloud)
