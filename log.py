import time
import socket
import os
import threading
import traceback
import sys
class UnSupportedMediaType(Exception):... #415
#404:FileNotFoundError
#403:PermissionError
class BadRequest(Exception):... # 400
class Log:
    def __init__(self):
        self.lock = threading.Lock()
        self.msg = ""
        timestamp = time.time()
        self.log_file = f"server_{time.strftime('%Y%m%d', time.gmtime(timestamp))}.log"
    def write_log(self, msg, critical=False):  # critical is true will stop the server
        timestamp = time.time()
        local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        utc_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))
        addr, exception = msg
        log_message = (
            f"UTC time: {utc_time}, local time: {local_time}, "
            f"address: {addr}, exception: {exception}\n"
        )
        with self.lock:  
                with open(self.log_file, 'a') as log:
                    log.write(log_message)
                    print(f"Log written to {self.log_file}")
        if critical:
            print(f"Critical error: happened in this thread, thread will stoped")
            log_message = "[CRITICAL] " + log_message  # sign as critical
            with self.lock: 
                with open(self.log_file, 'a') as log:
                    log.write(log_message)
            print(f"Log written to {self.log_file}")
            sys.exit(1)
            

