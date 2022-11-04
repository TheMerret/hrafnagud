import sys

from qtpy import QtWidgets

from hrafnagud.gui.mainwindow import MyMainWindow


def run_app():
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())