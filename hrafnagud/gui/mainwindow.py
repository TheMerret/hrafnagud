import pyvista as pv
import serial
import serial.tools.list_ports
from pyvistaqt import QtInteractor, MainWindow
from qtpy import QtWidgets, QtCore


class QDriverThread(QtCore.QThread):
    coordinatesReceived = QtCore.Signal(list, name="coordinatesReceived")

    def __init__(self, port, parent=None):
        super(QDriverThread, self).__init__(parent)
        self.port = port
        self.is_scanning = False

    def __del__(self):
        self.is_scanning = False
        if self.port is not None:
            self.port.close()
        self.wait()

    def run(self):
        # TODO: check for port is set
        # TODO: check if port is correct
        if not self.port.is_open:
            self.port.open()
        self.is_scanning = True
        while self.is_scanning:
            data = self.port.readline()
            if data:
                coordinates = self.process(data)
                self.coordinatesReceived.emit(coordinates)
                self.sleep(1)
            else:
                break

    @staticmethod
    def process(data):
        coordinates = [list(map(float, data.split()))]
        return coordinates


class QSetupDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO: oop data serialization
        self.conf = {
            "table_rotation": 1,
            "vertical_step": 1,
            "sensor_vertical": False,
            "sensor_vertical_step": None,
            "sensor_horizontal": True,
            "sensor_horizontal_step": 1
        }

        grid_layout = QtWidgets.QGridLayout()
        self.setLayout(grid_layout)
        self.rotation_label = QtWidgets.QLabel("Угол поворота", self)
        grid_layout.addWidget(self.rotation_label, 0, 0)
        self.rotation_spinbox = QtWidgets.QSpinBox(self)  # TODO: set max to 360
        grid_layout.addWidget(self.rotation_spinbox, 0, 1)
        self.vertical_move_label = QtWidgets.QLabel("Шаг по вертикали", self)
        grid_layout.addWidget(self.vertical_move_label, 1, 0)
        self.vertical_move_spinbox = QtWidgets.QSpinBox(self)
        grid_layout.addWidget(self.vertical_move_spinbox, 1, 1)
        self.sensors_group = QtWidgets.QGroupBox("Оси датчика", self)
        grid_box_layout = QtWidgets.QGridLayout()
        self.sensors_group.setLayout(grid_box_layout)
        # TODO: minimum 1 checkbox have to be checked
        self.sensor_vertical_checkbox = QtWidgets.QCheckBox("По вертикали", self)
        grid_box_layout.addWidget(self.sensor_vertical_checkbox, 0, 0)
        self.sensors_vertical_label = QtWidgets.QLabel("Шаг поворота")
        self.sensor_vertical_checkbox.stateChanged.connect(self.sensors_vertical_label.setEnabled)
        grid_box_layout.addWidget(self.sensors_vertical_label, 0, 1)
        self.sensor_vertical_spinbox = QtWidgets.QSpinBox(self)
        self.sensor_vertical_checkbox.stateChanged.connect(self.sensor_vertical_spinbox.setEnabled)
        self.sensor_vertical_checkbox.stateChanged.emit(False)
        grid_box_layout.addWidget(self.sensor_vertical_spinbox, 0, 2)
        self.sensor_horizontal_checkbox = QtWidgets.QCheckBox("По горизонтали", self)
        grid_box_layout.addWidget(self.sensor_horizontal_checkbox, 1, 0)
        self.sensors_horizontal_label = QtWidgets.QLabel("Шаг поворота")
        self.sensor_horizontal_checkbox.stateChanged.connect(self.sensors_horizontal_label.setEnabled)
        grid_box_layout.addWidget(self.sensors_horizontal_label, 1, 1)
        self.sensor_horizontal_spinbox = QtWidgets.QSpinBox(self)
        self.sensor_horizontal_checkbox.stateChanged.connect(self.sensor_horizontal_spinbox.setEnabled)
        self.sensor_horizontal_checkbox.stateChanged.emit(False)
        grid_box_layout.addWidget(self.sensor_horizontal_spinbox, 1, 2)
        grid_layout.addWidget(self.sensors_group, 2, 0, 1, 2)
        self.dialog_button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                            QtWidgets.QDialogButtonBox.Apply |
                                                            QtWidgets.QDialogButtonBox.Cancel)
        self.apply_btn = self.dialog_button_box.button(QtWidgets.QDialogButtonBox.Apply)
        self.dialog_button_box.accepted.connect(self.accept)
        self.dialog_button_box.rejected.connect(self.reject)
        self.dialog_button_box.clicked.connect(self.button_clicked)
        grid_layout.addWidget(self.dialog_button_box, 3, 0, 1, 2)

    def button_clicked(self, btn):
        if btn is self.apply_btn:
            # TODO: save conf to global data store
            self.conf = {
                "table_rotation": self.rotation_spinbox.value(),
                "vertical_step": self.vertical_move_spinbox.value(),
                "sensor_vertical": self.sensor_vertical_checkbox.isChecked(),
                "sensor_vertical_step": (self.sensor_vertical_spinbox.value()
                                         if self.sensor_vertical_checkbox.isChecked()
                                         else None),
                "sensor_horizontal": self.sensor_vertical_checkbox.isChecked(),
                "sensor_horizontal_step": (self.sensor_vertical_spinbox.value()
                                           if self.sensor_horizontal_checkbox.isChecked()
                                           else None),
            }
            self.accepted.emit()  # TODO: dedicated slot for apply


class HrafnagudMainWindow(MainWindow):
    PORT_BAUDRATE = 9600

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self, None)

        self.port = None
        self.driverThread = QDriverThread(self.port, self)
        self.driverThread.coordinatesReceived.connect(self.update_mesh)
        self.startAction = None
        self.stopAction = None
        self.setupAction = None

        self.pointsDockWidget = QtWidgets.QDockWidget(self)

        # add the pyvista interactor object
        self.plotter_points = QtInteractor()
        self.signal_close.connect(self.plotter_points.close)
        self.pointsDockWidget.setWidget(self.plotter_points)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.pointsDockWidget)

        self.surfaceDockWidget = QtWidgets.QDockWidget(self)

        # add the pyvista interactor object
        self.plotter_surface = QtInteractor()
        self.signal_close.connect(self.plotter_surface.close)
        self.surfaceDockWidget.setWidget(self.plotter_surface)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.surfaceDockWidget)

        self.load_menu()

    def load_menu(self):
        main_menu = self.menuBar()

        file_menu = main_menu.addMenu("File")

        meshes_menu = file_menu.addMenu('Meshes')
        show_points_action = QtWidgets.QAction('Show Points', self)
        show_points_action.setCheckable(True)
        show_points_action.triggered.connect(self.pointsDockWidget.setVisible)
        meshes_menu.addAction(show_points_action)
        show_points_action.setChecked(True)
        show_surface_action = QtWidgets.QAction('Show Surface', self)
        show_surface_action.setCheckable(True)
        show_surface_action.triggered.connect(self.surfaceDockWidget.setVisible)
        meshes_menu.addAction(show_surface_action)
        show_surface_action.setChecked(True)

        setting_submenu = file_menu.addMenu("Settings")
        ports_submenu = setting_submenu.addMenu("Ports")
        ports_action_group = QtWidgets.QActionGroup(ports_submenu)
        # TODO: add ability to update list of port with device is plugged in
        for com in serial.tools.list_ports.comports():
            comAction = ports_submenu.addAction(com.name)
            comAction.setCheckable(True)
            comAction.triggered.connect(self.set_comport)
            comAction.setActionGroup(ports_action_group)

        export_submenu = file_menu.addMenu("Export")
        stl_action = export_submenu.addAction("stl")
        stl_action.triggered.connect(self.export_stl)

        self.startAction = main_menu.addAction("Start")
        self.startAction.triggered.connect(self.start_scan)
        self.startAction.setDisabled(True)
        self.stopAction = main_menu.addAction("Stop")
        self.stopAction.triggered.connect(self.stop_scan)
        self.stopAction.setDisabled(True)

        self.setupAction = file_menu.addAction("Setup Scan")
        self.setupAction.triggered.connect(self.show_setup_dialog)

    def set_comport(self):
        # TODO: move port to driver and don't open without start
        self.port = serial.Serial(self.sender().text(), self.PORT_BAUDRATE)
        self.driverThread.port = self.port
        QtWidgets.QMessageBox.information(self, "Success!", f"{self.port.port} is set")
        # TODO: more casual showing start button
        self.startAction.setDisabled(False)

    def export_stl(self):
        save_path, _file_format = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        "Сохранить",
                                                                        ".",
                                                                        "STL (*.stl)")
        if not save_path:
            return
        (self.plotter_points.mesh + self.plotter_surface.mesh.extract_surface()).save(save_path)

    def start_scan(self):
        self.driverThread.start()
        self.startAction.setDisabled(True)
        self.stopAction.setDisabled(False)

    def stop_scan(self):
        self.driverThread.terminate()
        self.startAction.setDisabled(False)
        self.stopAction.setDisabled(True)

    def update_mesh(self, coordinates):
        self.plotter_points.add_points(pv.PolyData(coordinates))

    def show_setup_dialog(self):
        dlg = QSetupDialog(self)
        dlg.accepted.connect(self.update_scanning_settings)
        dlg.exec()

    def update_scanning_settings(self):
        print(self.sender().conf)
