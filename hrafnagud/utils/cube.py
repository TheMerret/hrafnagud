import math

import numpy as np

R = 4
CUBE_SIZE = 3
PRECISION = 45


def save_div(a: float, b: float) -> float:
    try:
        return a / b
    except ZeroDivisionError:
        return float("inf")


def polar_square_function(degree):
    degree = math.radians(degree)
    return R - min(save_div(CUBE_SIZE / 2, abs(math.cos(degree))),
                   save_div(CUBE_SIZE / 2, abs(math.sin(degree))))


def get_raw_layer(height, horizontal_degree, vertical_degree):
    # [degrees, height, horizontal_degree, vertical_degree, distance]
    return np.fromiter(
        ([d, height, horizontal_degree, vertical_degree, polar_square_function(d)] for d in
         np.arange(0, 360, PRECISION)), dtype=np.dtype((np.float64, 5)))


def get_layer_points(raw_layer):
    return np.fromiter((
        [
            R - R * math.cos(math.radians(degree)) + distance * math.cos(math.radians(degree)),
            R * math.sin(math.radians(degree)) - distance * math.sin(math.radians(degree)),
            height
        ] for degree, height, horizontal_degree, vertical_degree, distance in raw_layer),
        dtype=np.dtype((np.float64, 3))
    )


def get_cube_points():
    return np.vstack(get_layer_points(get_raw_layer(h, 0, 0)) for h in
                     np.arange(0, CUBE_SIZE + CUBE_SIZE / (360 / PRECISION),
                               CUBE_SIZE / (360 / PRECISION)))
