import math


class PointCloudGeneration:

    def __init__(self):
        self.scene_radius = 4  # TODO: get from global config

    def compute_point(self, scene_rotation, sensor_height, sensor_horizontal_rotation, sensor_vertical_rotation,
                      sensor_distance):
        if sensor_distance is None:
            return
        scene_rotation = math.radians(scene_rotation)
        sensor_horizontal_rotation = math.radians(sensor_horizontal_rotation)
        sensor_vertical_rotation = math.radians(sensor_vertical_rotation)
        x = (
                self.scene_radius *
                math.cos(scene_rotation) -
                sensor_distance *
                math.cos(scene_rotation + sensor_horizontal_rotation) *
                math.cos(sensor_vertical_rotation)
        )
        y = (
                self.scene_radius *
                math.sin(scene_rotation) *
                math.cos(sensor_vertical_rotation) -
                sensor_distance *
                math.sin(scene_rotation + sensor_horizontal_rotation)
        )
        z = sensor_height - sensor_height * math.sin(sensor_vertical_rotation)
        return [x, y, z]
