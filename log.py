import time
import socket
import os
import threading

class Log:
    def __init__(self):
        self.lock = threading.Lock()

    def write_log(self, msg):  # msg: [client_socket, addr, exception]
        timestamp = time.time()
        local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        utc_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))
        self.log_file = f"server_{time.strftime('%Y%m%d_%H%M%S', time.gmtime(timestamp))}.log"
        
        addr, exception = msg
        log_message = f"UTC time: {utc_time}, local time: {local_time}, address: {addr}, exception: {exception}\n"
        
        with open(self.log_file, 'w') as log:
            log.write(log_message)
        print(f"日志写入 {self.log_file}")
