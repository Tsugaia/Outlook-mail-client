import sys

from xmltools import *
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QDate

import numpy as np
import os, shutil
import calendar
import xml.etree.ElementTree as ET
from CustomTreeWidget import *
from CustomSearchWidget import *
import email, imaplib

import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        if (not os.path.exists('cred/users.npy') or not os.path.exists('cred/passwords.npy') or not os.path.exists('cred/servers.npy') or not os.path.exists('cred/fetchConditions.npy') or not os.path.exists('cred/names.npy')):
            users = np.array([])
            passwords = np.array([])
            servers = np.array([])
            fetchConditions = np.array([])
            names = np.array([])
            np.save('cred/users', users)
            np.save('cred/passwords', passwords)
            np.save('cred/servers', servers)
            np.save('cred/fetchConditions', fetchConditions)
            np.save('cred/names', names)

        self.initUI()

    def initUI(self): #inizializza l'interfaccia grafica della schermata principale
        loadUi("files/mainwindow_9.ui", self)
        self.setWindowTitle("Mail")
        self.treeWidget.setVisible(False)
        self.mailTab.tabCloseRequested.connect(self.draft)
        if np.size(np.load('cred/users.npy')) > 0: #se è presente almeno un utente riempi e mostra treeWidget
            users = np.load('cred/users.npy')
            passwords = np.load('cred/passwords.npy')
            servers = np.load('cred/servers.npy')
            names = np.load('cred/names.npy')
            fetchConditions = np.load('cred/fetchConditions.npy')
            self.accountButton.setText('loading...')
            makeXML(users, passwords, servers, names, fetchConditions)
            self.accountButton.setText('add account')
            self.makeTree()
            self.treeWidget.setVisible(True)
        self.show()

        # bottoni
        self.addButtonAnim(self.accountButton)
        self.accountButton.clicked.connect(self.login)
        self.addButtonAnim(self.deleteButton)
        self.deleteButton.clicked.connect(self.deleteAccount)
        self.addButtonAnim(self.refreshButton)
        self.refreshButton.clicked.connect(self.refresh)
        self.addButtonAnim(self.newButton)
        self.newButton.clicked.connect(self.newMail)
        self.addButtonAnim(self.searchButton)
        self.searchButton.clicked.connect(self.search)

    def login(self): #gestisce l'inserimento e l'eliminazione degli account
        loadUi("files/loginwindow.ui", self)
        self.setWindowTitle("Login")
        self.fromDateEdit.setDisplayFormat("dd.MM.yyyy")
        self.fromDateEdit.setFixedWidth(85)
        self.fromDateEdit.setMinimumDate(QDate.fromString("01.01.2020", "dd.MM.yyyy"))
        self.fromDateEdit.setMaximumDate(QDate(QDate.currentDate()))

        def goBack():
            self.initUI()

        self.addButtonAnim(self.closeButton)
        self.closeButton.clicked.connect(goBack)

        def checkCredentials():
            months = {str(index): month for index, month in enumerate(calendar.month_abbr) if month}
            server = self.serverLineEdit.text()
            user = self.emailLineEdit.text()
            password = self.passwordLineEdit.text()
            name = self.nameLineEdit.text()
            if self.allMailCheck.isChecked():
                fetchCond = 'NA'
            else:
                fetchCond = f'{self.fromDateEdit.date().day()}-{months[str(self.fromDateEdit.date().month())]}-{self.fromDateEdit.date().year()}'

            try:
                userArr = np.load('cred/users.npy')
                passwordArr = np.load('cred/passwords.npy')
                serverArr = np.load('cred/servers.npy')
                namesArr = np.load('cred/names.npy')
                fetchConditionsArr = np.load('cred/fetchConditions.npy')

                if user in userArr:
                    self.errorLine.setText('Account already present')
                    return

                con = imaplib.IMAP4_SSL(server)
                con.login(user, password)

                np.save('cred/users', np.append(userArr, user))
                np.save('cred/passwords', np.append(passwordArr, password))
                np.save('cred/servers', np.append(serverArr, server))
                np.save('cred/names', np.append(namesArr, name))
                np.save('cred/fetchConditions', np.append(fetchConditionsArr, fetchCond))

                self.errorLine.setText('Credentials saved! (super secure, trust me)')

            except imaplib.IMAP4.error: #errore di autenticazione
                self.errorLine.setText('Auth Error')
                return

            except Exception as ex:
                print(ex)
                self.errorLine.setText(str(ex).split(']')[-1])
                return

        self.addButtonAnim(self.loginButton)
        self.loginButton.clicked.connect(checkCredentials)

        def showPass(state): #checkbox "mostra password"

            if state == QtCore.Qt.Checked:
                self.passwordLineEdit.setEchoMode(QLineEdit.Normal)
            else:
                self.passwordLineEdit.setEchoMode(QLineEdit.Password)

        self.ShowPasswordCheck.stateChanged.connect(showPass)

        def allMail(state):
            if state == QtCore.Qt.Checked:
                self.fromDateEdit.setVisible(False)
            else:
                self.fromDateEdit.setVisible(True)

        self.allMailCheck.stateChanged.connect(allMail)

    def addButtonAnim(self, button): #cambio colore bottone alla pressione
        button.pressed.connect(lambda: button.setStyleSheet(
            'border:1px solid rgb(70, 70, 70) ;background-color: rgb(85, 85, 85); border-radius: 8px; padding: 3px; color: rgb(255, 255, 255)'))
        button.released.connect(lambda: button.setStyleSheet(
            'border:1px solid rgb(85, 85, 85) ;background-color: rgb(70, 70, 70); border-radius: 8px; padding: 3px; color: rgb(255, 255, 255)'))

    def makeTree(self): #popola treeWidget con i dati presenti in maildata.xml
        self.treeWidget.setColumnCount(1)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setAnimated(True)
        self.treeWidget.setIndentation(0)

        fnt = QFont('Open Sans', 9)
        fnt.setBold(True)

        tree = ET.parse('files/maildata.xml')
        root = tree.getroot()

        for user in root:
            Supparent = QTreeWidgetItem(self.treeWidget)
            Supparent.setText(0, user.tag)
            Supparent.setFont(0, fnt)
            for value in user:
                parent = QTreeWidgetItem(Supparent)
                parent.setText(0, value.tag)
                for sub in value:
                    child = QTreeWidgetItem(parent)
                    button = TreeWidget(sub.attrib['fromto'], sub.attrib['subject'], sub.attrib['ID'], self.mailTab, user.tag)
                    self.treeWidget.setItemWidget(child, 0, button)
                    button.procDone.connect(self.refresh)

    def refresh(self): #svuota e ri popola treeWidget
        self.treeWidget.clear()
        self.treeWidget.setVisible(False)
        users = np.load('cred/users.npy')
        passwords = np.load('cred/passwords.npy')
        servers = np.load('cred/servers.npy')
        names = np.load('cred/names.npy')
        fetchConditions = np.load('cred/fetchConditions.npy')
        self.refreshButton.setText('loading...')
        makeXML(users, passwords, servers, names, fetchConditions) #aggiorna maildata.xml
        self.refreshButton.setText('refresh')
        self.makeTree()
        self.treeWidget.setVisible(True)

    def deleteAccount(self): #gestisce la finestra di eliminazione di un utente
        dialog = QDialog()
        dialog.setFixedWidth(250)
        dialog.setFixedHeight(100)
        dialog.setWindowTitle('Delete account')
        dialog.setStyleSheet('background-color: rgb(53, 53, 53); color: rgb(255, 255, 255)')
        dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        layout = QGridLayout()
        dialog.setLayout(layout)

        comboBox = QComboBox()
        userArr = np.load('cred/users.npy')
        for x in userArr:
            comboBox.addItem(x)
        comboBox.setStyleSheet('border:1px solid rgb(85, 85, 85); border-radius: 8px; padding: 3px; background-color: rgb(70, 70, 70)')
        layout.addWidget(comboBox, 0, 0, 1, 0)

        deleteButton = QPushButton('delete')
        deleteButton.setStyleSheet('border:1px solid rgb(85, 85, 85); border-radius: 8px; padding: 3px; background-color: rgb(70, 70, 70)')
        self.addButtonAnim(deleteButton)
        deleteButton.clicked.connect(lambda: delete(str(comboBox.currentText())))
        layout.addWidget(deleteButton, 1, 0)

        closeButton = QPushButton('close')
        closeButton.setStyleSheet('border:1px solid rgb(85, 85, 85); border-radius: 8px; padding: 3px; background-color: rgb(70, 70, 70)')
        self.addButtonAnim(closeButton)
        closeButton.clicked.connect(dialog.close)
        layout.addWidget(closeButton, 1, 1)

        def delete(user): #effettua l'eliminazione dell'utente
            try:
                print(f'deleting {user}...')
                userArr = np.load('cred/users.npy')
                passwordArr = np.load('cred/passwords.npy')
                serverArr = np.load('cred/servers.npy')
                namesArr = np.load('cred/names.npy')
                fetchConditionsArr = np.load('cred/fetchConditions.npy')

                for i in range(np.size(userArr)): #elimina i dati dell'utente dagli array in cred/ (password, server, email, nome)
                    if userArr[i] == user:
                        np.save('cred/users', np.delete(userArr, i))
                        np.save('cred/passwords', np.delete(passwordArr, i))
                        np.save('cred/servers', np.delete(serverArr, i))
                        np.save('cred/fetchConditions', np.delete(fetchConditionsArr, i))
                        np.save('cred/names', np.delete(namesArr, i))

                shutil.rmtree('attachments/' + user.split('@')[0]) #rimuove le cartelle associate all'utente ed il loro contenuto
                shutil.rmtree('content/' + user.split('@')[0])
                shutil.rmtree('mail_ids/' + user.split('@')[0])

                deleteFromXML(user) #elimina dall'xml i dati relativi alle mail
                print('done')
                dialog.close()
                self.deleteButton.setText('loading...')
                self.refresh() #aggiorno treeWidget con i nuovi dati dell'xml
                self.deleteButton.setText('delete account')
            except Exception as ex:
                print(ex)

        dialog.exec_()

    def newMail(self): #gestisce la creazione di una nuova mail
        try:
            tabContent = tabWidget('', '', '', '', True, self.mailTab) #tab vuota, tosend=True per permettere di modificarne/salvarne il contenuto
            index = self.mailTab.addTab(tabContent, 'new mail')
            self.mailTab.setCurrentIndex(index)
        except Exception as ex:
            print(ex)

    def search(self): #gestisce la barra di ricerca
        param = self.searchLineEdit.text()
        if (param == '' or param == ' '):
            return
        elem = le.parse('files/maildata.xml').getroot()
        tempWidget = QWidget()
        tempWidget.setStyleSheet('border: 0px')
        layout = QVBoxLayout()
        layout.setSpacing(3)
        tempWidget.setLayout(layout)
        scrollArea = QScrollArea()
        scrollArea.setStyleSheet('border: 0px')

        for user in elem:
            for folder in user:
                for mail in folder:
                    if (param in mail.attrib['subject'] or param in mail.attrib['fromto']):
                        try:
                            layout.addWidget(SearchWidget(param, mail.attrib['subject'], mail.attrib['fromto'], user.tag, mail.attrib['content'], mail.attrib['path'], self.mailTab))
                        except Exception as ex:
                            print(ex)
        scrollArea.setWidget(tempWidget)

        index = self.mailTab.addTab(scrollArea, f'search: {param}')
        self.mailTab.setCurrentIndex(index)

    def draft(self, index): #gestisce le bozze
        def saveContent(ID): #salva il testo della bozza
            try:
                path = 'content/' + self.mailTab.widget(index).userComboBox.currentText().split('@')[0] + '/' + ID.split('-')[0] + '-' + ID.split('-')[1]
                with open(path, 'w') as f:
                    f.write(self.mailTab.widget(index).textEdit.toPlainText())
                return path
            except:
                return 'files/empty.txt'


        elem = et.parse('files/maildata.xml')

        if isinstance(self.mailTab.widget(index), QScrollArea): #se la tab è il risultato di una ricerca non occorre salvare nulla
            self.mailTab.removeTab(index)                       #(search è l'unica funzione a creare una tab contenente una QScrollArea)
            return

        if self.mailTab.widget(index).ID.split('-')[0] == 'draft': #se la tab contiene già una bozza salvo i cambiamenti
            for node in elem.find(self.mailTab.widget(index).userComboBox.currentText().split('@')[0]).find('DRAFT'):
                if node.attrib['ID'] == self.mailTab.widget(index).ID:
                    contentPath = saveContent(self.mailTab.widget(index).ID)
                    node.attrib['_from'] = self.mailTab.widget(index).userComboBox.currentText()
                    node.attrib['to'] = self.mailTab.widget(index).fromtoLine.text()
                    node.attrib['subject'] = self.mailTab.widget(index).subjectLine.text()
                    node.attrib['content'] = contentPath
                    node.attrib['path'] = ''
                    node.attrib['fromto'] = self.mailTab.widget(index).fromtoLine.text()
                    elem.write('files/maildata.xml')
            self.refresh()
        else:
            if self.mailTab.widget(index).tosend == True: #se la tab contiene una mail da inviare l'utente può scegliere di salvarla come bozza
                dialogue = QMessageBox()
                dialogue.setText('Do you want to save this email as draft?')
                dialogue.setStyleSheet('background-color: rgb(54, 54, 54); color: rgb(255, 255, 255);')

                yesButton = QPushButton('Yes')
                yesButton.setStyleSheet(
                    'background-color: rgb(70, 70, 70); border:1px solid rgb(85, 85, 85); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px')
                yesButton.pressed.connect(lambda: yesButton.setStyleSheet(
                    'border:1px solid rgb(70, 70, 70) ;background-color: rgb(85, 85, 85); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px'))
                yesButton.released.connect(lambda: yesButton.setStyleSheet(
                    'border:1px solid rgb(85, 85, 85) ;background-color: rgb(70, 70, 70); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px'))

                noButton = QPushButton('No')
                noButton.setStyleSheet(
                    'background-color: rgb(70, 70, 70); border:1px solid rgb(85, 85, 85); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px')
                noButton.pressed.connect(lambda: noButton.setStyleSheet(
                    'border:1px solid rgb(70, 70, 70) ;background-color: rgb(85, 85, 85); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px'))
                noButton.released.connect(lambda: noButton.setStyleSheet(
                    'border:1px solid rgb(85, 85, 85) ;background-color: rgb(70, 70, 70); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px'))

                dialogue.addButton(yesButton, QMessageBox.YesRole)
                dialogue.addButton(noButton, QMessageBox.NoRole)
                dialogue.setWindowTitle(' ')
                dialogue.setWindowFlags(QtCore.Qt.FramelessWindowHint)

                if dialogue.exec_() == 0:
                    try:
                        j = int(elem.getroot().find(self.mailTab.widget(index).userComboBox.currentText().split('@')[0]).attrib['draft_ID'])
                        contentPath = saveContent('draft' + '-' + str(j))
                        et.SubElement(
                            elem.find(self.mailTab.widget(index).userComboBox.currentText().split('@')[0]).find('DRAFT'),
                            'DRAFTMAIL',
                            ID='draft' + '-' + str(j) + '-' + self.mailTab.widget(index).userComboBox.currentText(), _from=self.mailTab.widget(index).userComboBox.currentText(),
                            to=self.mailTab.widget(index).fromtoLine.text(),
                            subject=self.mailTab.widget(index).subjectLine.text(),
                            content=contentPath,
                            path='', fromto=self.mailTab.widget(index).fromtoLine.text())
                        j = j + 1
                        elem.getroot().find(self.mailTab.widget(index).userComboBox.currentText().split('@')[0]).attrib['draft_ID'] = str(j)
                        elem.write('files/maildata.xml')
                        self.refresh()
                    except Exception as ex:
                        print(ex)

        self.mailTab.removeTab(index)

app = QApplication([])
window = MainWindow()
app.exec_()