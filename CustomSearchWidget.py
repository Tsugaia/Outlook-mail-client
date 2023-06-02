from tabContent import *

class SearchWidget(QWidget):

    def __init__(self, param, subject, fromto, user, contentPath, attachmentsPath, tab):
        super().__init__()
        self.initUI(param, subject, fromto, user)
        self.subject = subject
        self.fromto = fromto
        self.contentPath = contentPath
        self.attachmentsPath = attachmentsPath
        self.tab = tab
        self.tosend = False
        self.ID = 'search-NA'

    def initUI(self, param, subject, fromto, user):

        def color(fromto, subject, param): #colora il testo corrispondente al criterio di ricerca
            text = f'{fromto}: {subject}'
            Ctext = '<br>'
            textArr = text.split(param)
            for i in range(len(textArr)):
                if len(textArr) - i > 1:
                    Ctext += textArr[i] + f'<b style="color: #0000FF;">{param}</b>'
                else:
                    Ctext += textArr[i]
            return Ctext

        label = QLabel(f'({user}) ' + color(fromto, subject,param))
        label.setStyleSheet('color: rgb(255, 255, 255);background-color: rgb(70, 70, 70) ;border-radius: 5px; border: 1px solid rgb(70, 70, 70); padding: 3px')
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(label)

    def mousePressEvent(self, event): #apri la tab corrispondente alla mail selezionata
        tabContent = tabWidget(self.fromto, self.subject, self.contentPath, self.attachmentsPath, False, self.tab)
        index = self.tab.addTab(tabContent, self.subject)
        self.tab.setCurrentIndex(index)