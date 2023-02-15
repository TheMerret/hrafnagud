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

    def connect(self):
        self.driver.board.connect()

    def start(self):
        if not self.is_scanning:
            self.is_scanning = True
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
        self.driver.stop()
        self.driver.board.disconnect()

    def capture(self):
        while self.is_scanning:
            captures = self.capture_points()
            print(captures)
            if captures is None:
                self.stop()
                break
            for c in captures:
                self.captures_queue.put(c)

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
        try:
            point = self.point_cloud_generation.compute_point(
                scene_rotation=capture["sceneAngle"],
                sensor_height=capture["height"],
                sensor_horizontal_rotation=capture["horizontalAngle"],
                sensor_vertical_rotation=capture["verticalAngle"],
                sensor_distance=capture["distance"],
            )
        except Exception:
            point = None
        if point is None:
            return
        self.point_cloud_callback(point)

    def set_settings(self, settings):
        self.driver.set_setting_field("MAX_SCENE_ROTATION_STEP", settings["MAX_SCENE_ROTATION_STEP"])
        self.driver.set_setting_field("MAX_SCENE_ROTATION", settings["MAX_SCENE_ROTATION"])
        self.driver.set_setting_field("SENSOR_HEIGHT_STEP", settings["SENSOR_HEIGHT_STEP"])
        self.driver.set_setting_field("SCENE_ROTATION_STEP", settings["SCENE_ROTATION_STEP"])
        scanning_direction = ""
        if settings["SENSOR_HORIZONTAL_DIRECTION"] and settings["SENSOR_VERTICAL_DIRECTION"]:
            scanning_direction = "both"
        elif settings["SENSOR_HORIZONTAL_DIRECTION"]:
            scanning_direction = "horizontally"
        elif settings["SENSOR_VERTICAL_DIRECTION"]:
            scanning_direction = "vertically"
        self.driver.set_setting_field("SCANNING_DIRECTION", scanning_direction)
        self.driver.set_setting_field("SENSOR_HORIZONTAL_ROTATION_STEP",
                                      settings["SENSOR_HORIZONTAL_ROTATION_STEP"])
        self.driver.set_setting_field("SENSOR_VERTICAL_ROTATION_STEP",
                                      settings["SENSOR_VERTICAL_ROTATION_STEP"])
        self.driver.set_setting_field("MAX_SENSOR_VERTICAL_ROTATION",
                                      settings["MAX_SENSOR_VERTICAL_ROTATION"])
        self.driver.set_setting_field("SENSOR_MAX_HEIGHT", settings["SENSOR_MAX_HEIGHT"])
