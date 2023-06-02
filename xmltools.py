import imaplib, email, os, glob, re
import xml.etree.ElementTree as et
import lxml.etree as le
import sys
import numpy as np
import pickle
import sklearn
from PyQt5 import QtCore

pattern_uid = re.compile(b'\d+ \(UID (?P<uid>\d+)\)')

def makeXML(users, password, imap_url, names, fetchConditions): #aggiorna il contenuto dell'xml con i dati delle nuove mail
    try:
        print('in func makeXML...')
        xml_doc = et.parse('files/maildata.xml')
        filename = 'files/finalized_model.sav' #modello addestrato del filtro anti spam
        filename_fe = 'files/finalized_fe.sav' #modello addestrato feature extraction (serve a permettere l'analisi del testo di una mail da parte del filtro)
        model = pickle.load(open(filename, 'rb'))
        feature_extraction = pickle.load(open(filename_fe, 'rb'))

        index = 0
        for user in users:
            QtCore.QCoreApplication.processEvents()
            if len(xml_doc.getroot().findall(user.split('@')[0])) <= 0: #se un utente non esiste nell'xml lo crea
                _ = et.SubElement(xml_doc.getroot(), user.split('@')[0], spam_ID="0" ,draft_ID="0")

            con = imaplib.IMAP4_SSL(imap_url[index])
            con.login(user, password[index])

            path = 'content/' + user.split('@')[0]
            attachment_dir = 'attachments/' + user.split('@')[0]
            id_dir = 'mail_ids/' + user.split('@')[0]
            spam_id = int(xml_doc.getroot().find(user.split('@')[0]).attrib['spam_ID'])

            folders = searchInboxes(con)

            if not os.path.exists(path):
                os.mkdir(path)

            if not os.path.exists(attachment_dir):
                os.mkdir(attachment_dir)

            if not os.path.exists(id_dir):
                os.mkdir(id_dir)

            for dir in xml_doc.getroot().findall(user.split('@')[0]):
                if dir.find('SPAM') is None:
                    _ = et.SubElement(xml_doc.find(user.split('@')[0]), 'SPAM')
                if dir.find('DRAFT') is None:
                    _ = et.SubElement(xml_doc.find(user.split('@')[0]), 'DRAFT')

            for folder in folders:
                print('*', end='')

                con.select(folder)
                if fetchConditions[index] == 'NA':
                    status, data = con.search(None, '(ALL)')
                else:
                    status, data = con.search(None, '(ALL)', f'(SENTSINCE {fetchConditions[index]})')
                mail_ids = []
                for block in data:
                    mail_ids += block.split()

                if mail_ids == []:
                    continue

                QtCore.QCoreApplication.processEvents()
                for dir in xml_doc.getroot().findall(user.split('@')[0]):
                    if dir.find(folder) is None:
                        _ = et.SubElement(xml_doc.find(user.split('@')[0]), folder)

                idPath = 'mail_ids/' + user.split('@')[0] + '/' + folder

                if not os.path.exists(idPath):
                    os.mkdir(idPath)

                newId = np.array(mail_ids)
                if os.path.exists(idPath + '/IdList.npy'):
                    oldId = np.load(idPath + '/IdList.npy')

                    newId = np.setdiff1d(newId, oldId)
                    np.save(idPath + '/IdList', np.concatenate((newId, oldId)))
                else:
                    np.save(idPath + '/IdList', newId)

                for i in newId:
                    QtCore.QCoreApplication.processEvents()
                    print(f'[{i}, {folder}]', end='')
                    result, data = con.fetch(i, '(RFC822)')
                    raw = email.message_from_bytes(data[0][1])

                    Content = get_body(raw).decode('utf-8')

                    tmp_folder = folder

                    try:
                        if folder != 'Sent':
                            input_data_features = feature_extraction.transform([Content])
                            prediction = model.predict(input_data_features)
                            if prediction[0] == 1:
                                folder = 'SPAM'
                                i = spam_id
                                spam_id = spam_id + 1
                                xml_doc.getroot().find(user.split('@')[0]).attrib['spam_ID'] = str(spam_id)
                    except Exception as ex:
                        print(ex)

                    f = open('content/' + user.split('@')[0] + '/' + folder + '-' + str(i), 'w')
                    f.write(Content)
                    f.close()

                    contentPath = 'content/' + user.split('@')[0] + '/' + folder + '-' + str(i)
                    From, To, Subject = return_data(raw)
                    PathArr = get_attachments(raw, attachment_dir, folder + '-' + str(i))
                    Path = ''
                    for path in PathArr:
                        Path = Path + ',' + path
                    Path = Path[1:]

                    if user not in To:
                        fromto = To
                    else:
                        fromto = From

                    et.SubElement(xml_doc.find(user.split('@')[0]).find(folder),
                                  fromto.split("@")[0].replace('<', '').replace('>', '').replace(' ', ''),
                                  ID=folder + '-' + str(i), _from=From, to=To, subject=Subject, content=contentPath,
                                  path=str(Path), fromto=fromto)

                    folder = tmp_folder
            index = index + 1

            con.close()
        print('\n makeXML done')
        xml_doc.write('files/maildata.xml')
    except Exception as ex:
        print(ex)

def get_body(b): #estrae il testo di una mail
    body = ""

    if b.is_multipart():
        for part in b.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            #salta ogni allegato di tipo text/plain (txt)
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body = part.get_payload(decode=True)  # decode
                break
    # non multipart - quindi plain text, no allegati
    else:
        body = b.get_payload(decode=True)
    return body

def get_attachments(msg, path, id):
    filePath = []
    j = 0
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        fileName = part.get_filename()

        if bool(fileName):
            fullPath = path + '/' + id +'/'
            filePath.append(fullPath + fileName)
            if not os.path.exists(fullPath):
                os.mkdir(fullPath)
        with open(filePath[j], 'wb') as f:
            f.write(part.get_payload(decode = True))
        j = j + 1
    return filePath

def return_data(msg): #restituisce i dati principali di una mail
    return decode_mime_words(msg.get('From')).split('<')[-1].replace('>',''), decode_mime_words(msg.get('To')).split('<')[-1].replace('>',''), decode_mime_words(msg.get('Subject'))

def searchInboxes(mail): #restituisce tutte le inbox di un account
    list = mail.list()[1]
    l = []
    for folder in list:
        l.append(folder.decode().split(' "/" ')[1])
    return l

def decode_mime_words(s): #decodifica MIME encoded-words
    return u''.join(
        word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
        for word, encoding in email.header.decode_header(s))

def searchID(id, user): #ricerca per ID mail
    elem = le.parse('files/maildata.xml').getroot()

    for user in elem.find(user):
        for node in user:
            if node.attrib['ID'] == id:
                contentPath = node.attrib['content']
                attachmentPath = node.attrib['path']
    return contentPath, attachmentPath

def deleteFromXML(user): #elimina i dati di un utente dall'xml
    try:
        with open('files/maildata.xml', 'r') as f:
            doc = le.parse(f)
            for element in doc.getroot().findall(user.split('@')[0]):
                doc.getroot().remove(element)
            doc.write('files/maildata.xml')
    except Exception as ex:
        print(ex)

def searchInXML(param, tab): #ricerca per parametro
    elem = le.parse('files/maildata.xml').getroot()

    for user in elem:
        for folder in user:
            for mail in folder:
                if (param in mail.attrib['subject'] or param in mail.attrib['fromto']):
                     print(f'{user.tag}: \n{mail.attrib["ID"]}\n{mail.attrib["subject"]}\n')