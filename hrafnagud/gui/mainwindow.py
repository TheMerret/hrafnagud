from qtpy import QtWidgets, QtCore
import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow
from serial.tools.list_ports import comports as list_comports

from hrafnagud.utils.cube import get_cube_points


class MyMainWindow(MainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self, None)

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

        self.add_meshes()

    def add_meshes(self):
        """ add a mesh to the pyqt frame """
        points = get_cube_points()
        point_cloud = pv.PolyData(points)
        self.plotter_points.add_mesh(point_cloud)
        self.plotter_points.reset_camera()

        surface = point_cloud.delaunay_3d()
        self.plotter_surface.add_mesh(surface, show_edges=True)

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
        for com in list_comports():
            comAction = portsSubmenu.addAction(com.name)
            comAction.setCheckable(True)
            comAction.triggered.connect(self.set_comport)

        exportSubmenu = fileMenu.addMenu("Export")
        stlAction = exportSubmenu.addAction("stl")
        stlAction.triggered.connect(self.export_stl)

    def set_comport(self):
        # FIXME: multiple ports can be set
        dlg = QtWidgets.QMessageBox(self)
        dlg.setWindowTitle("Success!")
        dlg.setText(f"{self.sender().text()} is set")
        button = dlg.exec()

        if button == QtWidgets.QMessageBox.Ok:
            return

    def export_stl(self):
        save_path, _file_format = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                        "Сохранить",
                                                                        ".",
                                                                        "STL (*.stl)")
        if not save_path:
            return
        (self.plotter_points.mesh + self.plotter_surface.mesh.extract_surface()).save(save_path)