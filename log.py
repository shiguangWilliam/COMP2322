import time
import socket
import os
import threading
class Log:
    def init__(self):
        pass
    def write_log(self, msg): #msg:[client_socket,addr,exception]
        timestamp = time.time()
        local_time = time.localtime(timestamp)
        utc_time = time.gmtime(timestamp)
        self.log_file = f"server_{utc_time}.log"
        addr = msg[1]
        with open(self.log_file,'w') as log:
            log.write(f"UTC Time: {utc_time}, Local Time: {local_time}, Message: {msg}\n")
        print(f"Log written to {self.log_file}")
    