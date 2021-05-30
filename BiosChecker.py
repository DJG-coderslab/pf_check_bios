#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
aplikacja do sprawdzania wersji biosu, uruchamina w WinPE
na sprawdzanym komputerze
zwraca informacje:
- bios poprawny
- bios niepoprawny
- po cichu zapisuje do bazy, to tabeli tmp PN, których nie ma w tablei PN
'''

import pymysql
import re
import sys
import wmi

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MainWindow(QMainWindow):
    to_close = False
    def __init__(self):
        super().__init__()
        self.bios_result = '_'
        self.device = device()
        self.initUI()
       
    def initUI(self):
        self.resize(300,200)
        self._center()
        self.setWindowTitle('BIOS Checker (alpha)')
        self.build_window()
       
    def build_window(self):
        if not self.device.is_sn_correct():
            _msg = 'SN: {} \nis not valid as an ACER SN\n Check the DMI'.format(self.device.get_sn_mb())
            _color = 'color: blue; background: red' 
        else:
            if self.device.is_bios_correct():
                _msg = 'Bios: ' + self.device.get_bios_mb() + ' \nis correct'
                _color = 'color:yellow; background: green'
            else:
                if self.device.is_pn_in_db():
                    _msg = 'Bios: ' + self.device.get_bios_mb() + ' \nis not correct! \
                           \nIt should be: ' + self.device.get_bios_db()
                    _color = 'color: blue; background: red' 
                else:
                    self.device.add_to_db()
                    sys.exit()
        
        _font = QFont('Serif', 17, QFont.Bold)
        message = QLabel(_msg)
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet(_color) 
        message.setFont(_font)
        
        _button = QPushButton ('Exit', self)
        _button.clicked.connect(self._btn_pressed)
        
        main_widget = QWidget()
        
        layout = QVBoxLayout()
        layout.addWidget(message)
        layout.addWidget(_button)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
    
    def _btn_pressed(self):
        self.close()
    
    def _center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape or e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.close()

class device():

    server_db = '10.***REMOVED***'
    data_base = 'BiosChecker'
    user_db = 'bios'
    pass_db = '***REMOVED***'
    __debug = False

    def __init__(self):
        c = wmi.WMI()
        wql = 'select * from Win32_bios'
        for i in c.query(wql):
            self.serial_number = i.SerialNumber.strip()
            self.part_number = self.serial_number[0:10]
            self.bios_mb = i.SMBIOSBIOSVersion.strip()

    def open_db(self):
        self.connect = pymysql.connect(host=device.server_db, user=device.user_db,
                                  passwd=device.pass_db, db=device.data_base)
        self. cursor = self.connect.cursor()
        return self.cursor

    def close_db(self):
        self.cursor.close()
        self.connect.close()

    def info(self):
        print("PN: {} \nSN: {}".format(self.part_number, self.serial_number))

    def is_pn_in_db(self):
        """zapytanie powinno zwrócic nic lub dokładnie jeden element part_number,
        w bazie nie może byc dwóch takich samych PN"""

        sql = 'select PN from PN where PN = "{}"'.format(self.part_number)
        back = False
        result = ''
        self.open_db()
        try:
            self.cursor.execute(sql)
            self.connect.commit()
            result = self.cursor.fetchone()
            self.close_db()
            if result is not None:
                back = True
            else:
                """nie ma w bazie takiego PN"""
                back = False
        except Exception as err:
            self.close_db()
            print("Something went wrong: {}".format(err))
        return back

    def get_bios_mb(self):
        if re.search ('^v\d+', self.bios_mb, flags=re.I):
            self.bios_mb = self.bios_mb[1:]
        return self.bios_mb

    def get_sn_mb(self):
        return self.serial_number

    def get_bios_db(self):
        sql = '''select project.bios_version from PN join model on PN.ID_model=model.ID
                 join project on model.ID_project=project.ID
                 where PN.PN = "{}"'''.format(self.part_number)
        self.open_db()
        try:
            self.cursor.execute(sql)
            self.connect.commit()
            bios_db = self.cursor.fetchone()[0]
            self.close_db()
        except Exception as err:
            self.close_db()
            print("Something went wrong: {}".format(err))
        return bios_db

    def add_to_db(self):
        self.open_db()
        sql = '''select PN from PN where PN like  "{}%"'''.format(self.part_number)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
            if self.cursor.fetchone() is not None:
                pass
            else:
                sql = '''insert into tmp (SerialNumber, BiosVersion)
                         values ('{}', '{}')'''.format(self.part_number, 'NEW')
                try:
                    self.cursor.execute(sql)
                    self.connect.commit()
                    self.close_db()
                except Exception as err:
                    self.close_db()
                    if device.__debug:
                        print("Something went wrong: {}".format(err))
                    else:
                        pass
        except Exception as err:
            print(err)

    def is_bios_correct(self):
        if self.is_pn_in_db():
            if re.match(self.get_bios_db(), self.get_bios_mb(), flags=0):
                back = True
            else:
                back = False
        else:
            back = False
        return back

    def is_sn_correct(self):
        '''check if SN from bios is correct:
           - it's 22 digits
           - starts from letter
           - there isn't any space'''
        result = False
        if (re.match(r'^[A-Z]\w{21}$', self.serial_number, flags=0)):
            result = True
        return result


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()