import os
import sys
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
import PyQt5
import pywintypes
import win32api,win32con

from Ui_uart_tool_ui import Ui_MainWindow
from uart import Uart
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton)
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import QTextCursor, QIcon
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import QTimer

import datetime
import logging

from tool_log import tool_log

class MyPyQT_Form(QMainWindow, Ui_MainWindow):

    uart_recv_updata_show_data_signal = pyqtSignal(str)
    uart_updata_recv_num_signal = pyqtSignal(int)
    uart_updata_send_num_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # 创建串口对象
        self.uart = Uart(self)

        self.setWindowTitle("串口工具")

        self.uart_com_run_status = 0 # 串口运行状态
        self.uart_data_rec_count = 0
        self.uart_data_send_count = 0

        # 定时器
        self.uart_timer_num = 1000
        self.uart_timer_line_edit.setText('1000')
        self.uart_timer_send = QTimer()
        self.uart_timer_send.timeout.connect(self.uart_timer_send_cb)

        #log init
        self.log = tool_log(self)

        # 设定默认值
        self.baud_combo_box.setCurrentText(str(9600))
        self.stopbit_combo_box.setCurrentText(str(1))
        self.databit_combo_box.setCurrentText(str(8))
        self.checkbit_combo_box.setCurrentText(str(None))
        self.rec_ascii_radio_button.setChecked(1)
        self.rec_hex_radio_button.setChecked(0)
        self.send_ascii_radio_button.setChecked(1)
        self.send_hex_radio_button.setChecked(0)
        self.uart_send_show.setFocusPolicy(QtCore.Qt.StrongFocus)

        # 绑定事件
        self.uart_en_push_button.clicked.connect(self.uart_en_push_button_cb)
        self.uart_clear_rec_push_button.clicked.connect(self.uart_clear_rec_push_button_cb)
        self.uart_send_push_button.clicked.connect(self.uart_send_push_button_cb)
        self.uart_send_clear_push_button.clicked.connect(self.uart_send_clear_push_button_cb)

        self.rec_ascii_radio_button.toggled.connect(self.uart_ascii_to_hex_rec_radio_button_cb) 
        self.rec_hex_radio_button.toggled.connect(self.uart_hex_to_ascii_rec_radio_button_cb)
        self.send_ascii_radio_button.toggled.connect(self.uart_ascii_to_hex_send_radio_button_cb) 
        self.send_hex_radio_button.toggled.connect(self.uart_hex_to_ascii_send_radio_button_cb)
        
        self.uart_recv_updata_show_data_signal.connect(self.update_uart_recv_show_cb)
        self.uart_updata_recv_num_signal.connect(self.update_uart_recv_num_show_cb)
        self.uart_updata_send_num_signal.connect(self.update_uart_send_num_show_cb)

        self.timestamp_check_box.clicked.connect(self.uart_timestamp_en_check_box_cb)

        self.uart_timer_line_edit.setValidator(QIntValidator(1, 1000000))
        self.uart_timer_line_edit.textChanged.connect(self.uart_set_send_time_line_edit_cb)
        self.uart_timer_check_box.clicked.connect(self.uart_time_en_check_box_cb)


    def uart_en_push_button_cb(self):
        if self.uart_com_run_status == 0:
            port = self.com_combo_box.currentText()
            if port == '':
                win32api.MessageBox(0, "请选择串口", "警告",win32con.MB_ICONWARNING)
                return
            baud = self.baud_combo_box.currentText()
            stopbit = self.stopbit_combo_box.currentText()
            databit = self.databit_combo_box.currentText()
            checkbit = self.checkbit_combo_box.currentText()
            self.uart.uart_init(port, baud, stopbit, databit, checkbit)
            self.log.tool_log_init()
            self.log.tool_log_log(port + baud)
            if self.uart.err == -1:
                self.uart_com_run_status = 0
                win32api.MessageBox(0, port+"已被使用", "警告",win32con.MB_ICONWARNING)
            else:
                self.uart_com_run_status = 1
                self.uart.open_uart_thread()
                self.uart_en_push_button.setText('关闭串口')
                self.log.tool_log_open_thread()
        else:
            self.uart_com_run_status = 0
            self.uart.close_uart_thread()

            if self.uart_timer_send.isActive() == True: # 更改定时器运行时间时如果还开着定时器，则重新打开
                self.uart_timer_check_box.setChecked(False)
                self.uart_timer_send.stop()
            self.uart_en_push_button.setText('打开串口')

    # new add
    def uart_send_check_value(self, data):
        databit = self.databit_combo_box.currentText()
        max_data = 0
        if databit == '8':
            max_data = 256
        elif databit == '7':
            max_data = 128
        elif databit == '6':
            max_data = 64
        else:
            max_data = 32

        cin_temp = ''
        for item in data.split(' '):
            current_item = ''
            item_int = -1
            item_int = int(item, 16)
            while item_int > (max_data - 1):
                current_item = ' ' + hex(int(item_int % max_data)) + current_item
                item_int = int(item_int / max_data)
            if item_int != -1:
                current_item = ' ' + hex(int(item_int % max_data)) + current_item
            cin_temp += current_item

        return cin_temp

    def uart_send_hex_pack(self, item):
        toSend = 0
        databit = self.databit_combo_box.currentText()
        if item != '':
            toSend = int(item[2:], 16)

            if toSend > 255 and databit == '8':
                # print_time_stamp()  # print timestamp
                # print_fatal(hex(toSend) + ' does not fit in a byte! This shouldn\'t happen!')
                toSend = ''
            elif toSend > 127 and databit == '7':
                # print_time_stamp()  # print timestamp
                # print_fatal(hex(toSend) + ' does not fit in 7 bits! This shouldn\'t happen!')
                toSend = ''
            elif toSend > 63 and databit == '6':
                # print_time_stamp()  # print timestamp
                # print_fatal(hex(toSend) + ' does not fit in 6 bits! This shouldn\'t happen!')
                toSend = ''
            elif toSend > 31 and databit == '5':
                # print_time_stamp()  # print timestamp
                # print_fatal(hex(toSend) + ' does not fit in 5 bits! This shouldn\'t happen!')
                toSend = ''
            return toSend
        else:
            return item

    def uart_send_push_button_cb(self):
        if self.uart_com_run_status == 0:
            return
        send_data = ''
        send_text = self.uart_send_show.toPlainText()
        print("send_text")
        print(send_text)
        if send_text == '':
            return

        send_data_str = ''
        send_str_list = 'send: '
        if self.send_hex_radio_button.isChecked() == True:  # 十六进制发送
            # hex_send_text = self.hex2bin(send_text.replace(' ', ''))
            send_data_str = self.uart_send_check_value(send_text)  # new add
            print('send_data_str:')
            print(send_data_str)
            cin = send_data_str.strip()
            toSend = 0
            for item in cin.split(' '):
                toSend = self.uart_send_hex_pack(item)
                if toSend == '':
                    continue
                send_str_list += item
                send_str_list += '\t'
                send_data = toSend.to_bytes(1, 'little')
                self.uart.uart_send_func(send_data)
            # send_data = bytes(hex_send_text,encoding='utf-8')
            print(send_str_list)
            if send_str_list != '':
                send_data_list = 'send: '
                send_data_list += send_text
                self.log.tool_log_log(send_data_list)
        else:
            send_data = send_text.encode()
            self.uart.uart_send_func(send_data)
            if send_data != '':
                send_data_list = 'send: '
                send_data_list += send_data
                self.log.tool_log_log(send_data_list)
                

    def uart_clear_rec_push_button_cb(self):
        self.uart_data_rec_count = 0
        self.uart_rx_data_count_label.setText(str(self.uart_data_rec_count))
        self.uart_rec_show.clear()


    def uart_send_clear_push_button_cb(self):
        self.uart_data_send_count = 0
        self.uart_tx_data_count_label.setText(str(self.uart_data_send_count))
        self.uart_send_show.clear()

    def uart_timestamp_en_check_box_cb(self):
        if self.timestamp_check_box.isChecked() == True:
            self.uart.uart_time_stamp(1)
        else:
            self.uart.uart_time_stamp(0)

    def hex2bin(self, str):
        bits = ''
        for x in range(0, len(str), 2):
            bits += chr(int(str[x:x+2], 16))
        return bits

    def uart_ascii_to_hex_rec_radio_button_cb(self):
        if self.rec_ascii_radio_button.isChecked() == True:
            self.uart.uart_set_rec_hex_lock(0)
        else:
            return
    
    def uart_hex_to_ascii_rec_radio_button_cb(self):
        if self.rec_hex_radio_button.isChecked() == True:
            self.uart.uart_set_rec_hex_lock(1)
        else:
            return

    def uart_ascii_to_hex_send_radio_button_cb(self):
        if self.send_ascii_radio_button.isChecked() == True:
                self.uart_send_hex_lock = 0
                send_text = self.uart_send_show.toPlainText().replace(' ', '')
                self.uart_send_show.clear()
                hex_send_text = self.hex2bin(send_text)
                self.uart_send_show.setText(hex_send_text)
        else:
            return

    def uart_hex_to_ascii_send_radio_button_cb(self):
        if self.send_hex_radio_button.isChecked() == True:
            self.uart_send_hex_lock = 1
            text_list = []
            send_text = bytes(self.uart_send_show.toPlainText(), encoding='utf-8')
            for i in range(len(send_text)):
                text_list.append(hex(send_text[i])[2:])
            send_text_to_hex = ' '.join(text_list)
            self.uart_send_show.clear()
            self.uart_send_show.setText(send_text_to_hex)
        else:
            return


    def update_uart_recv_show_cb(self, data):
        print('update_uart_recv_show_cb data is :')
        print(data)
        rec_data_list = 'recive: '
        rec_data_list += data
        self.log.tool_log_log(rec_data_list)

        data += '\n'
        self.uart_rec_show.insertPlainText(data)
        cursor = self.uart_rec_show.textCursor()
        self.uart_rec_show.moveCursor(cursor.End)

    def update_uart_recv_num_show_cb(self, data_num):
        self.uart_data_rec_count += data_num
        self.uart_rx_data_count_label.setText(str(self.uart_data_rec_count))


    def update_uart_send_num_show_cb(self, data_num):
        self.uart_data_send_count += data_num
        self.uart_tx_data_count_label.setText(str(self.uart_data_send_count))


    def uart_set_send_time_line_edit_cb(self):
        if self.uart_timer_line_edit.text() == '0':
            self.uart_timer_line_edit.setText('1000')
            self.uart_timer_num = 1000
            win32api.MessageBox(0, "请输入1-1000000范围内的值", "警告",win32con.MB_ICONWARNING)
        else:
            self.uart_timer_num = self.uart_timer_line_edit.text()
        
        if self.uart_timer_send.isActive() == True: # 更改定时器运行时间时如果还开着定时器，则重新打开
            self.uart_timer_send.stop()
            self.uart_timer_send.start(int(self.uart_timer_num))
    
    def uart_timer_send_cb(self):
        self.uart_send_push_button_cb()
    
    def uart_time_en_check_box_cb(self):
        if self.uart_com_run_status == 0:
            self.uart_timer_check_box.setChecked(False)
            return None

        if self.uart_timer_check_box.isChecked() == True:
            self.uart_timer_send.start(int(self.uart_timer_num))
        else:
            self.uart_timer_send.stop()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_pyqt_form = MyPyQT_Form()
    my_pyqt_form.show()
    sys.exit(app.exec_())
