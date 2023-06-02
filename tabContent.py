import os.path
import smtplib
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QTextEdit, QGridLayout, \
    QFileDialog, QLabel, QHBoxLayout, QMessageBox, QComboBox, QDialog
from PyQt5.QtGui import QFont, QColor, QWindow
from PyQt5 import QtCore
from xmltools import searchID
import ast
import shutil
from CustomAttachmentLabel import *
import xml.etree.ElementTree as et

class tabWidget(QWidget):

    procDone = QtCore.pyqtSignal(str)

    def __init__(self, fromto = '', subject = '', content= '', attachmentPath = '',tosend = False, tabWidget = None, ID = ''):
        super().__init__()
        self.msg = MIMEMultipart()
        self.content = content
        self.attachmentPath = attachmentPath
        self.tosend = tosend
        self.ID = ID
        self.tabWidget = tabWidget
        self.initUI(fromto, subject, content, tosend, attachmentPath)

    @QtCore.pyqtSlot()
    def refreshSignal(self):
        self.procDone.emit('R')

    def initUI(self, fromto, subject, content, tosend, attachmentPath): #inizializza la UI
        grid = QGridLayout()
        self.setLayout(grid)
        self.setStyleSheet("color: rgb(255, 255, 255); background-color:rgb(70, 70, 70)")

        self.attachLine = QLineEdit('Attachments:')
        self.attachLine.setReadOnly(True)

        self.sendButton = QPushButton('Send')
        self.addButtonAnim(self.sendButton)

        self.attachButton = QPushButton('Attach')
        self.addButtonAnim(self.attachButton)

        self.fwdButton = QPushButton('Forward')
        self.addButtonAnim(self.fwdButton)

        self.reButton = QPushButton('Respond')
        self.addButtonAnim(self.reButton)

        self.fromtoLine = QLineEdit(fromto)
        self.fromtoLine.setStyleSheet(
            'border:1px solid rgb(85, 85, 85); border-radius: 8px; padding: 3px; background-color: rgb(70, 70, 70); color: rgb(255, 255, 255)')
        self.fromtoLine.setEnabled(False)

        self.subjectLine = QLineEdit(subject)
        self.subjectLine.setStyleSheet(
            'border:1px solid rgb(85, 85, 85); border-radius: 8px; padding: 3px; background-color: rgb(70, 70, 70); color: rgb(255, 255, 255)')
        self.subjectLine.setEnabled(False)

        self.textEdit = QTextEdit()
        self.textEdit.setStyleSheet(
            'border:1px solid rgb(85, 85, 85); border-radius: 8px; padding: 3px; background-color: rgb(70, 70, 70); color: rgb(255, 255, 255)')

        if (self.content != '' and self.content != ' '):
            with open(self.content, 'r') as f:
                for line in f:
                    self.textEdit.append(line)

        if tosend == True: #se è una mail da inviare abilita userComboBox la quale permetterà di scegliere l'indirizzo dal quale inviare la mail
            self.userComboBox = QComboBox()

            users = np.load('cred/users.npy')
            for user in users:
                self.userComboBox.addItem(user)

            if self.ID.split('-')[0] == 'draft':
                index = self.userComboBox.findText(self.ID.split('-')[-1], QtCore.Qt.MatchFixedString) #mostra l'indirizzo giusto nella comboBox
                if index >= 0:
                    self.userComboBox.setCurrentIndex(index)
                    self.userComboBox.setEnabled(False)

            grid.addWidget(self.userComboBox, 0, 0, 1, 0)
            grid.addWidget(self.fromtoLine, 1, 0, 1, 0)
            grid.addWidget(self.subjectLine, 2, 0, 1, 0)
            grid.addWidget(self.textEdit, 3, 0, 1, 0)

            grid.addWidget(self.attachLine, 4, 0, 1, 0)
            grid.addWidget(self.attachButton, 5, 0)
            grid.addWidget(self.sendButton, 5, 1)

            self.sendButton.clicked.connect(lambda: self.sendMail(self.fromtoLine.text(), self.subjectLine.text(), self.textEdit.toPlainText()))
            self.attachButton.clicked.connect(lambda: self.attach('NA'))


            self.fromtoLine.setEnabled(True)
            self.subjectLine.setEnabled(True)
            self.textEdit.setReadOnly(False)

        else:
            grid.addWidget(self.fromtoLine, 0, 0, 1, 0)
            grid.addWidget(self.subjectLine, 1, 0, 1, 0)
            grid.addWidget(self.textEdit, 2, 0, 1, 0)

            self.fwdButton.clicked.connect(self.forward)
            self.reButton.clicked.connect(self.respond)
            self.textEdit.setReadOnly(True)

            if attachmentPath != "":
                ind = 0
                l = QLabel('Attachments:')
                l.setStyleSheet('border-radius: 0px; border: 0px; background-color: rgb(54, 54, 54)')
                grid.addWidget(l, 3, 0, 1, 0)
                for file in attachmentPath.split(','):
                    grid.addWidget(labelWidget(file), 4, ind)
                    ind = ind + 1

                grid.addWidget(self.fwdButton, 5, 0, 1, (ind + 1) / 2)
                grid.addWidget(self.reButton, 5, (ind + 1) / 2, 1, (ind + 1) / 2)
            else:
                grid.addWidget(self.fwdButton, 4, 0)
                grid.addWidget(self.reButton, 4, 1)

    def sendMail(self, to, subject, content): #gestisce l'invio delle mail

        def deleteDraft(ID, user): #elimina il messaggio dalle bozze quando inviato
            with open('files/maildata.xml', 'r') as f:
                elem = et.parse(f)
                for node in elem.getroot().find(user).find('DRAFT'):
                    if node.attrib['ID'] == ID:
                        elem.getroot().find(user).find('DRAFT').remove(node)
                elem.write('files/maildata.xml')

                path = 'content/' + user + '/' + ID.split('-')[0] + '-' + ID.split('-')[1]
                if os.path.exists(path):
                    os.remove(path)
            self.refreshSignal()

        user = self.userComboBox.currentText()
        users = np.load('cred/users.npy')
        passwords = np.load('cred/passwords.npy')
        servers = np.load('cred/servers.npy')
        names = np.load('cred/names.npy')
        index = 0
        for i in range(np.size(users)):
            if users[i] == user:
                index = i
                break

        dialogue = QMessageBox()
        dialogue.setText('  Do you want to send this email?')
        dialogue.setStyleSheet('background-color: rgb(54, 54, 54); color: rgb(255, 255, 255);')

        yesButton = QPushButton('Yes')
        yesButton.setStyleSheet('background-color: rgb(70, 70, 70); border:1px solid rgb(85, 85, 85); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px')
        yesButton.pressed.connect(lambda: yesButton.setStyleSheet(
            'border:1px solid rgb(70, 70, 70) ;background-color: rgb(85, 85, 85); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px'))
        yesButton.released.connect(lambda: yesButton.setStyleSheet(
            'border:1px solid rgb(85, 85, 85) ;background-color: rgb(70, 70, 70); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px'))

        noButton = QPushButton('No')
        noButton.setStyleSheet('background-color: rgb(70, 70, 70); border:1px solid rgb(85, 85, 85); border-radius: 8px; padding-left: 50px; padding-right: 50px; padding-top: 3px; padding-bottom: 3px')
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
                server = smtplib.SMTP(servers[index])
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(user, passwords[index])


                self.msg['From'] = names[index] + ' <' + user + '>'
                self.msg['To'] = to
                self.msg['Subject'] = subject
                self.msg.attach(MIMEText(content, 'plain'))
                print(f'from: {self.msg["From"]}, to: {self.msg["To"]}, subject: {self.msg["Subject"]}')

                text = self.msg.as_string()
                print('step-1')
                server.sendmail(user, to, text)
                print('step-2')
                self.msg = MIMEMultipart()

                self.attachLine.setText('Attachments:')
                print('done')
                server.close()

                if self.ID.split('-')[0] == 'draft':
                    print('deleting draft...')
                    deleteDraft(self.ID, self.ID.split('-')[-1].split('@')[0])
                    print('done!')
                self.tabWidget.removeTab(self.tabWidget.currentIndex())

            except smtplib.SMTPAuthenticationError:
                print('Auth error')
                return
            except Exception as ex:
                print('Error')
                print(ex)
                return

    def attach(self, path = 'NA'): #gestisce gli allegati
        try:
            if path == 'NA':
                options = QFileDialog.Options()
                filenames, _ = QFileDialog.getOpenFileNames(self, 'Open file', '', 'All Files (*.*)', options=options)
            else:
                filenames = []
                for part in path.split(','):
                    filenames.append(part)

            if filenames != []:
                for filename in filenames:
                    print(filename, '-')
                    attachment = open(filename, 'rb')
                    filename = filename[filename.rfind("/") + 1:]

                    p = MIMEBase('application', 'octet-stream')
                    p.set_payload(attachment.read())
                    encoders.encode_base64(p)
                    p.add_header("Content-Disposition", f"attachment; filename={filename}")

                    self.msg.attach(p)
                    if not self.attachLine.text().endswith(':'):
                        self.attachLine.setText(self.attachLine.text() + ',')
                    self.attachLine.setText(self.attachLine.text() + ' ' + filename)
        except Exception as ex:
            print(ex)

    def addButtonAnim(self, button):
        button.setStyleSheet('background-color: rgb(70, 70, 70); border:1px solid rgb(85, 85, 85); border-radius: 8px; padding: 3px')
        button.pressed.connect(lambda: button.setStyleSheet(
            'border:1px solid rgb(70, 70, 70) ;background-color: rgb(85, 85, 85); border-radius: 8px; padding: 3px'))
        button.released.connect(lambda: button.setStyleSheet(
            'border:1px solid rgb(85, 85, 85) ;background-color: rgb(70, 70, 70); border-radius: 8px; padding: 3px'))

    def forward(self): #funzione "inoltra"
        def add_tab(to):
            try:
                tabContent = tabWidget(to, 'fwd: ' + self.subjectLine.text(), self.content, '', True)
                if os.path.exists(self.attachmentPath):
                    tabContent.attach(self.attachmentPath)
                index = self.tabWidget.addTab(tabContent, 'fwd: ' + self.subjectLine.text())
                self.tabWidget.setCurrentIndex(index)
                dialog.close()
            except Exception as ex:
                print(ex)

        dialog = QDialog()
        dialog.setFixedWidth(250)
        dialog.setFixedHeight(100)
        dialog.setWindowTitle('Forward')
        dialog.setStyleSheet('background-color: rgb(53, 53, 53); color: rgb(255, 255, 255)')
        dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        layout = QGridLayout()
        dialog.setLayout(layout)
        toLineEdit = QLineEdit()
        toLineEdit.setStyleSheet(
            'border:1px solid rgb(85, 85, 85); border-radius: 8px; padding: 3px; background-color: rgb(70, 70, 70); color: rgb(255, 255, 255)')
        layout.addWidget(toLineEdit, 1, 0, 1, 0)
        selectButton = QPushButton('select')
        self.addButtonAnim(selectButton)
        closeButton = QPushButton('close')
        self.addButtonAnim(closeButton)
        layout.addWidget(selectButton, 2, 0)
        layout.addWidget(closeButton, 2, 1)
        closeButton.clicked.connect(dialog.close)
        selectButton.clicked.connect(lambda: add_tab(toLineEdit.text()))

        dialog.exec_()

    def respond(self): #funzione "rispondi"
        tabContent = tabWidget(self.fromtoLine.text(), 're: ' + self.subjectLine.text(), '', '', True)
        index = self.tabWidget.addTab(tabContent, 're: ' + self.subjectLine.text())
        self.tabWidget.setCurrentIndex(index)