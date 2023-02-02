import pyvista as pv
import serial
import serial.tools.list_ports
from pyvistaqt import QtInteractor, MainWindow
from qtpy import QtWidgets, QtCore

from hrafnagud.core.scan import Scan


class QScannerThread(QtCore.QThread):
    coordinatesReceived = QtCore.Signal(list, name="coordinatesReceived")

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.scan = Scan()
        self.scan.driver.board.port_name = port
        self.scan.point_cloud_callback = self.coordinatesReceived.emit
        self.finished.connect(self.stop)

    def set_scanner_port(self, port):
        self.scan.driver.board.port_name = port

    def stop(self):
        # TODO: control stop/start menu action buttons
        self.scan.stop()

    def run(self):
        # TODO: handle exceptions to ?dialog
        self.parent().startAction.setDisabled(True)
        self.parent().stopAction.setDisabled(False)
        self.scan.start()
        self.scan.join_processes()
        self.parent().startAction.setDisabled(False)
        self.parent().stopAction.setDisabled(True)

    def set_settings(self, settings):
        self.scan.set_settings(settings)


class QSetupDialog(QtWidgets.QDialog):
    changesApplied = QtCore.Signal(name="changesApplied")

    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO: oop data serialization
        self.conf = {
            "MAX_SCENE_ROTATION_STEP": 30,
            "MAX_SCENE_ROTATION": 180,
            "SENSOR_HEIGHT_STEP": 1,
            "SCENE_ROTATION_STEP": 1,
            "SENSOR_HORIZONTAL_DIRECTION": True,
            "SENSOR_HORIZONTAL_ROTATION_STEP": 1,
            "SENSOR_VERTICAL_DIRECTION": False,
            "SENSOR_VERTICAL_ROTATION_STEP": 1,
            "MAX_SENSOR_VERTICAL_ROTATION": 45,
            "SENSOR_MAX_HEIGHT": 3,
        }

        grid_layout = QtWidgets.QGridLayout()
        self.setLayout(grid_layout)
        row_ind = 0
        self.phase_rotation_label = QtWidgets.QLabel("Шаг фазы", self)
        grid_layout.addWidget(self.phase_rotation_label, row_ind, 0)
        self.phase_rotation_spinbox = QtWidgets.QSpinBox(self)
        self.phase_rotation_spinbox.setValue(self.conf["MAX_SCENE_ROTATION_STEP"])
        grid_layout.addWidget(self.phase_rotation_spinbox, row_ind, 1)
        row_ind += 1
        self.max_scene_rotation_label = QtWidgets.QLabel("Максимальный поворот стола", self)
        grid_layout.addWidget(self.max_scene_rotation_label, row_ind, 0)
        self.max_scene_rotation_spinbox = QtWidgets.QSpinBox(self)
        self.max_scene_rotation_spinbox.setMaximum(360)
        self.max_scene_rotation_spinbox.setValue(self.conf["MAX_SCENE_ROTATION"])
        grid_layout.addWidget(self.max_scene_rotation_spinbox, row_ind, 1)
        row_ind += 1
        self.scene_rotation_label = QtWidgets.QLabel("Шаг поворота стола", self)
        grid_layout.addWidget(self.scene_rotation_label, row_ind, 0)
        self.scene_rotation_spinbox = QtWidgets.QSpinBox(self)
        self.scene_rotation_spinbox.setValue(self.conf["SCENE_ROTATION_STEP"])
        grid_layout.addWidget(self.scene_rotation_spinbox, row_ind, 1)
        row_ind += 1
        self.sensor_height_step_label = QtWidgets.QLabel("Шаг по высоте", self)
        grid_layout.addWidget(self.sensor_height_step_label, row_ind, 0)
        self.sensor_height_step_spinbox = QtWidgets.QSpinBox(self)
        self.sensor_height_step_spinbox.setValue(self.conf["SENSOR_HEIGHT_STEP"])
        grid_layout.addWidget(self.sensor_height_step_spinbox, row_ind, 1)
        row_ind += 1
        self.max_height_label = QtWidgets.QLabel("Максимальная высота", self)
        grid_layout.addWidget(self.max_height_label, row_ind, 0)
        self.max_height_spinbox = QtWidgets.QSpinBox(self)
        self.max_height_spinbox.setValue(self.conf["SENSOR_MAX_HEIGHT"])
        grid_layout.addWidget(self.max_height_spinbox, row_ind, 1)
        row_ind += 1
        self.max_vertical_rotation_label = QtWidgets.QLabel("Максимальный поворот по вертикали",
                                                            self)
        grid_layout.addWidget(self.max_vertical_rotation_label, row_ind, 0)
        self.max_vertical_rotation_spinbox = QtWidgets.QSpinBox(self)
        self.max_vertical_rotation_spinbox.setValue(self.conf["MAX_SENSOR_VERTICAL_ROTATION"])
        grid_layout.addWidget(self.max_vertical_rotation_spinbox, row_ind, 1)
        row_ind += 1
        self.sensors_group = QtWidgets.QGroupBox("Оси датчика", self)
        grid_box_layout = QtWidgets.QGridLayout()
        self.sensors_group.setLayout(grid_box_layout)
        self.sensor_vertical_checkbox = QtWidgets.QCheckBox("По вертикали", self)
        self.sensor_vertical_checkbox.stateChanged.connect(self.keep_sensors_checked)
        grid_box_layout.addWidget(self.sensor_vertical_checkbox, 0, 0)
        self.sensors_vertical_label = QtWidgets.QLabel("Шаг поворота")
        self.sensor_vertical_checkbox.stateChanged.connect(self.sensors_vertical_label.setEnabled)
        grid_box_layout.addWidget(self.sensors_vertical_label, 0, 1)
        self.sensor_vertical_spinbox = QtWidgets.QSpinBox(self)
        self.sensor_vertical_spinbox.setValue(self.conf["SENSOR_VERTICAL_ROTATION_STEP"])
        self.sensor_vertical_checkbox.stateChanged.connect(self.sensor_vertical_spinbox.setEnabled)
        self.sensor_vertical_checkbox.stateChanged.emit(False)
        grid_box_layout.addWidget(self.sensor_vertical_spinbox, 0, 2)
        self.sensor_horizontal_checkbox = QtWidgets.QCheckBox("По горизонтали", self)
        self.sensor_horizontal_checkbox.stateChanged.connect(self.keep_sensors_checked)
        grid_box_layout.addWidget(self.sensor_horizontal_checkbox, 1, 0)
        self.sensors_horizontal_label = QtWidgets.QLabel("Шаг поворота")
        self.sensor_horizontal_checkbox.stateChanged.connect(self.sensors_horizontal_label.setEnabled)
        grid_box_layout.addWidget(self.sensors_horizontal_label, 1, 1)
        self.sensor_horizontal_spinbox = QtWidgets.QSpinBox(self)
        self.sensor_horizontal_spinbox.setValue(self.conf["SENSOR_HORIZONTAL_ROTATION_STEP"])
        self.sensor_horizontal_checkbox.stateChanged.connect(self.sensor_horizontal_spinbox.setEnabled)
        self.sensor_horizontal_checkbox.setChecked(True)
        grid_box_layout.addWidget(self.sensor_horizontal_spinbox, 1, 2)
        grid_layout.addWidget(self.sensors_group, row_ind, 0, 1, 2)
        row_ind += 1
        self.dialog_button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                            QtWidgets.QDialogButtonBox.Apply |
                                                            QtWidgets.QDialogButtonBox.Cancel)
        self.apply_btn = self.dialog_button_box.button(QtWidgets.QDialogButtonBox.Apply)
        self.dialog_button_box.accepted.connect(self.accept)
        self.dialog_button_box.rejected.connect(self.reject)
        self.dialog_button_box.clicked.connect(self.button_clicked)
        grid_layout.addWidget(self.dialog_button_box, row_ind, 0, 1, 2)

    def button_clicked(self, btn):
        if btn is self.apply_btn:
            # TODO: save conf to global data store
            self.conf = {
                "MAX_SCENE_ROTATION_STEP": self.phase_rotation_spinbox.value(),
                "MAX_SCENE_ROTATION": self.max_scene_rotation_spinbox.value(),
                "SENSOR_HEIGHT_STEP": self.sensor_height_step_spinbox.value(),
                "SCENE_ROTATION_STEP": self.scene_rotation_spinbox.value(),
                "SENSOR_HORIZONTAL_DIRECTION": self.sensor_horizontal_checkbox.isChecked(),
                "SENSOR_HORIZONTAL_ROTATION_STEP": self.sensor_horizontal_spinbox.value(),
                "SENSOR_VERTICAL_DIRECTION": self.sensor_vertical_checkbox.isChecked(),
                "SENSOR_VERTICAL_ROTATION_STEP": self.sensor_vertical_spinbox.value(),
                "MAX_SENSOR_VERTICAL_ROTATION": self.max_vertical_rotation_spinbox.value(),
                "SENSOR_MAX_HEIGHT": self.max_height_spinbox.value(),
            }
            self.changesApplied.emit()

    def keep_sensors_checked(self):
        sensor_checkboxes = [i for i in self.sensors_group.children() if isinstance(i, QtWidgets.QCheckBox)]
        checked_checkboxes = [i for i in sensor_checkboxes if i.isChecked()]
        if len(checked_checkboxes) == 1:
            # if checked checkbox is single
            checked_checkboxes[0].setDisabled(True)
        else:
            for cbox in sensor_checkboxes:
                cbox.setDisabled(False)


class HrafnagudMainWindow(MainWindow):
    PORT_BAUDRATE = 9600

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self, None)

        self.port = None
        self.driverThread = QScannerThread(self.port, self)
        self.driverThread.coordinatesReceived.connect(self.update_mesh)
        self.connectAction = None
        self.startAction = None
        self.stopAction = None
        self.setupAction = None

        self.pointsDockWidget = QtWidgets.QDockWidget(self)

        # add the pyvista interactor object
        self.plotter_points = QtInteractor()
        self.signal_close.connect(self.plotter_points.close)
        self.pointsDockWidget.setWidget(self.plotter_points)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.pointsDockWidget)

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

        self.connectAction = main_menu.addAction("Connect")
        self.connectAction.triggered.connect(self.connect_scan)
        self.connectAction.setDisabled(True)
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
        port = self.sender().text()
        self.driverThread.set_scanner_port(port)
        QtWidgets.QMessageBox.information(self, "Success!", f"{port} is set")
        # TODO: more casual showing start button
        self.connectAction.setDisabled(False)

    def export_stl(self):
        save_path, _file_format = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        "Сохранить",
                                                                        ".",
                                                                        "STL (*.stl)")
        if not save_path:
            return
        self.plotter_points.mesh.save(save_path)

    def connect_scan(self):
        self.driverThread.scan.connect()
        self.connectAction.setDisabled(True)
        self.startAction.setDisabled(False)

    def start_scan(self):
        self.driverThread.start()

    def stop_scan(self):
        self.driverThread.stop()

    def update_mesh(self, point):
        self.plotter_points.add_points(pv.PolyData(point))

    def show_setup_dialog(self):
        dlg = QSetupDialog(self)
        dlg.changesApplied.connect(self.update_scanning_settings)
        dlg.exec()

    def update_scanning_settings(self):
        self.driverThread.set_settings(self.sender().conf)
