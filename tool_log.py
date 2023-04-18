
import logging
import queue
import threading
import datetime

class tool_log_Thread(threading.Thread):
    def __init__(self, cur_self, main_self):
        super(tool_log_Thread, self).__init__()
        self.cur_self = cur_self
        self.main_self = main_self
        self.thread = threading.Event()

    def stop(self):
        self.thread.set()

    def stopped(self):
        return self.thread.is_set()

    def run(self):
        while True:
            if self.stopped():
                break
            time = ''
            try:
                if False == self.cur_self.log_queue.empty():
                    log_data_str = ''
                    log_data = self.cur_self.log_queue.get()
                    # time = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S:%f]\r\n')
                    print('tool_log_Thread: log_data')
                    print(log_data)
                    log_data = log_data.replace('\r', '')
                    logging.debug(log_data)
                    # self.cur_self.log
                    # data_num = len(send_data)
                    # # 统计发送字符的数量
                    # self.main_self.uart_updata_send_num_signal.emit(data_num)
                    # #ascii 发送
                    # self.cur_self.serial.write(send_data)
                else:
                    continue
            except queue.Empty:
                continue

class tool_log(object):
    def __init__(self, parent):
        self.parent = parent
        self.log_queue = queue.Queue(1000)

    def tool_log_init(self, file_name):
        # self.log = logging.basicConfig(filename = file_name, encoding = 'utf-8', format='%(asctime)s %(levelname)s:%(message)s', level = logging.DEBUG)
        print('tool_log_init file_name:')
        print(file_name)
        logging.basicConfig(filename='log_file.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
        self.log_thread = tool_log_Thread(self, self.parent)

    def tool_log_open_thread(self):
        self.log_thread.start()

    def tool_log_close_thread(self):
        self.log_thread.close()

    def tool_log_log(self, data):
        self.log_queue.put(data)
