import serial


class Board:

    def __init__(self, parent=None):
        self.parent = parent
        self.port_name = None
        self.baud_rate = 9600  # TODO: get from global settings
        self.serial_port = None

    def connect(self):
        self.serial_port = serial.Serial(self.serial_port, self.baud_rate)

    def disconnect(self):
        self.serial_port.close()

    def motor_move(self, step=0):
        self.send_command(f"5,0,{step}")

    def send_command(self, request):
        self.serial_port.write(request)


class Lasers:
    # TODO: class for each laser or move to board class

    def __init__(self, board):
        self.board = board
        self.sensor_height = 0
        self.sensor_horizontal_rotation = 0
        self.sensor_vertical_rotation = 0

    def capture_lasers(self):
        self.board.serial_port.write("8")
        distance_right = self.board.serial_port.read()
        while not distance_right:
            distance_right = self.board.serial_port.read()
        self.board.serial_port.write("9")
        distance_left = self.board.serial_port.read()
        while not distance_left:
            distance_left = self.board.serial_port.read()
        right = [
            self.sensor_height,
            self.sensor_horizontal_rotation,
            self.sensor_vertical_rotation,
            distance_right
        ]
        left = [
            self.sensor_height,
            self.sensor_horizontal_rotation,
            self.sensor_vertical_rotation,
            distance_left
        ]
        return [right, left]


class Driver:

    def __init__(self):
        self.board = Board(self)