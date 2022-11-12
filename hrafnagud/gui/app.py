import sys

from qtpy import QtWidgets

from hrafnagud.gui.mainwindow import HrafnagudMainWindow


def run_app():
    app = QtWidgets.QApplication(sys.argv)
    window = HrafnagudMainWindow()
    window.show()
    sys.exit(app.exec_())