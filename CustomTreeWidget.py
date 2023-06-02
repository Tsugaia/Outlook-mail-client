import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QTextEdit, QGridLayout, QLabel
from PyQt5.QtGui import QFont, QColor
from PyQt5 import QtCore
from tabContent import *

class TreeWidget(QWidget):

    procDone = QtCore.pyqtSignal(str)

    def __init__(self, fromto, subject, ID, tab, user):
        super().__init__()
        self.initUI(fromto, subject)

        self.id = ID
        self.tab = tab
        self.user = user
        self.fromto = fromto
        self.subject = subject

    def mousePressEvent(self, event): #quando un elemento del treeWidget viene selezionato occorre creare una nuova tab
        tosend = False
        print(f"ph'nglui mglw'nafh {self.id} R'lyeh wgah'nagl fhtagn")
        if self.id.split('-')[0] == 'draft':
            tosend = True
        contentPath, attachmentsPath = searchID(self.id, self.user)
        tabContent = tabWidget(self.fromto, self.subject, contentPath, attachmentsPath, tosend, self.tab, self.id)
        index = self.tab.addTab(tabContent, self.subject)
        self.tab.setCurrentIndex(index)
        try:
            tabContent.procDone.connect(self.refreshSignal)
        except Exception as ex:
            print(ex)

    @QtCore.pyqtSlot()
    def refreshSignal(self):
        self.procDone.emit('R')


    def initUI(self, fromto, subject):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        fromtoline = QLabel(f'<{fromto.split("@")[0]}> {subject}')
        fromtoline.setStyleSheet("QLabel::hover"
                            "{"
                            "background-color :  257AFD;" #selection blue
                            "}")
        self.setStyleSheet('border:1px; border-radius: 0px;')

        layout.addWidget(fromtoline)