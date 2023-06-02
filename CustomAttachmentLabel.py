import shutil

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFileDialog


class labelWidget(QWidget):

    def __init__(self, path = ''):
        super().__init__()

        self.path = path

        self.initUI()

    def initUI(self):
        try:
            layout = QHBoxLayout()
            layout.setContentsMargins(0,0,0,0)
            layout.setSpacing(0)
            self.setLayout(layout)
            self.attachmentLabel = QLabel(f'<a href="not a link but it works">{self.path.split("/")[-1]}</a>')
            self.attachmentLabel.setStyleSheet('border-radius: 0px; border: 0px; background-color: rgb(54, 54, 54)')
            self.attachmentLabel.linkActivated.connect(lambda: self.download(self.path))
            layout.addWidget(self.attachmentLabel)
        except Exception as ex:
            print(ex)

    def download(self, file): #effettua il download dell'allegato
        folderPath = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folderPath:
            shutil.copy(file, folderPath) #in realtà effettuo solo una copia nella cartella selezionata
                                          #poichè gli allegati vengono scaricati in fase di scansione della casella postale