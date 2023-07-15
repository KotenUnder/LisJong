import LisJong

import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *



class GUIPlayer(LisJong.Janshi):
    def __init__(self):
        super()

    def engine_discard(self, draw_pai_, riichi_=[], tsumo_=False, kong_=[]):
        # 並び替えして、手札とつも灰を表示する
        pass


    def engine_call(self, discarded_, choice_, message_):
        pass



class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.test = QCheckBox('test', self)
        self.setGeometry(300, 50, 1200, 1400)
        self.setWindowTitle('QCheckBox')




if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
