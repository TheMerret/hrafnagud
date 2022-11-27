import math


class ImageCapture:

    def __init__(self, driver):
        self.driver = driver

    def capture_lasers(self):
        captures = self.driver.lasers.capture()
        return captures


class PointCloudGeneration:

    def __init__(self):
        self.scene_radius = 20  # TODO: get from global config

    def compute_point_cloud(self, scene_rotation, sensors_data):
        point_cloud = []
        for ind, sensor_data in enumerate(sensors_data):
            point_cloud.append(self.compute_point(scene_rotation, sensor_data, ind))
        return point_cloud

    def compute_point(self, scene_rotation, sensor_data, index):
        (
            sensor_height,
            sensor_horizontal_rotation,
            sensor_vertical_rotation,
            sensor_distance
        ) = sensor_data
        scene_rotation = math.radians(scene_rotation + 180 * index)
        sensor_horizontal_rotation = math.radians(sensor_vertical_rotation)
        sensor_vertical_rotation = math.radians(sensor_vertical_rotation)
        x = (
                self.scene_radius -
                self.scene_radius *
                math.cos(scene_rotation) +
                sensor_distance *
                math.cos(sensor_horizontal_rotation) *
                math.cos(sensor_vertical_rotation) *
                math.cos(scene_rotation)
        )
        y = (
                self.scene_radius * math.sin(scene_rotation) -
                sensor_distance *
                math.cos(sensor_horizontal_rotation) *
                math.cos(sensor_vertical_rotation) *
                math.sin(scene_rotation) +
                sensor_distance *
                math.sin(sensor_horizontal_rotation)
        )
        z = sensor_height - sensor_height * math.sin(sensor_vertical_rotation)
        return [x, y, z]
