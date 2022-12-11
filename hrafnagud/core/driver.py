import struct

import serial


class Board:

    def __init__(self, parent=None):
        self.parent = parent
        self.port_name = None
        self.baud_rate = 9600  # TODO: get from global settings
        self.serial_port = None

    def connect(self):
        if self.port_name is None:
            raise Exception("Port is not set")  # TODO: use dedicated exception
        self.serial_port = serial.Serial(self.port_name, self.baud_rate)
        # handshake
        self.serial_port.read()  # TODO: normal handshake
        self.serial_port.timeout = 2

    def disconnect(self):
        self.serial_port.close()

    def send_command(self, request):
        self.serial_port.write(request)


class Driver:

    def __init__(self):
        self.board = Board(self)
        self.scanning_data_structure = struct.Struct("f4f4f")

    def capture_data(self):
        raw_data = self.board.serial_port.read(self.scanning_data_structure.size)
        try:
            data = self.scanning_data_structure.unpack(raw_data)
        except struct.error:
            data = None  # TODO: raise dedicated error
        return data

    def start(self):
        self.board.send_command(b"1")  # TODO: command as constant
