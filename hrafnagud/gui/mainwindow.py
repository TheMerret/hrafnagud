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


class HrafnagudMainWindow(MainWindow):
    PORT_BAUDRATE = 9600

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self, None)

        self.port = None
        self.driverThread = QDriverThread(self.port, self)
        self.driverThread.coordinatesReceived.connect(self.update_mesh)
        self.startAction = None
        self.stopAction = None

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
        mainMenu = self.menuBar()

        fileMenu = mainMenu.addMenu("File")

        meshesMenu = fileMenu.addMenu('Meshes')
        showPointsAction = QtWidgets.QAction('Show Points', self)
        showPointsAction.setCheckable(True)
        showPointsAction.triggered.connect(self.pointsDockWidget.setVisible)
        meshesMenu.addAction(showPointsAction)
        showPointsAction.setChecked(True)
        showSurfaceAction = QtWidgets.QAction('Show Surface', self)
        showSurfaceAction.setCheckable(True)
        showSurfaceAction.triggered.connect(self.surfaceDockWidget.setVisible)
        meshesMenu.addAction(showSurfaceAction)
        showSurfaceAction.setChecked(True)

        settingSubmenu = fileMenu.addMenu("Settings")
        portsSubmenu = settingSubmenu.addMenu("Ports")
        portsActionGroup = QtWidgets.QActionGroup(portsSubmenu)
        # TODO: add ability to update list of port with device is plugged in
        for com in serial.tools.list_ports.comports():
            comAction = portsSubmenu.addAction(com.name)
            comAction.setCheckable(True)
            comAction.triggered.connect(self.set_comport)
            comAction.setActionGroup(portsActionGroup)

        exportSubmenu = fileMenu.addMenu("Export")
        stlAction = exportSubmenu.addAction("stl")
        stlAction.triggered.connect(self.export_stl)

        self.startAction = mainMenu.addAction("Start")
        self.startAction.triggered.connect(self.start_scan)
        self.startAction.setDisabled(True)
        self.stopAction = mainMenu.addAction("Stop")
        self.stopAction.triggered.connect(self.stop_scan)
        self.stopAction.setDisabled(True)

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
