import socket
import threading
import json
import os
import time
from log import Log
from myhttp import HTTP_Request, HTTP_Response, FileHandler
class Server:
    def __init__(self):
        json_file = "config.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                config = json.load(f)
                self.host = config
                self.port = config
        else:
            print(f"Configuration file {json_file} not found. Using default values.")
            self.host = "127.0.0.1"
            self.port = 8080
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def start(self):
        self.server_socket.bind((self.host, self.port))#listening on socket
        self.server_socket.listen(5) #max 5 sequence of connections
        print(f"Server started on {self.host}:{self.port}")
        while True:
            client_socket,addr = self.server_socket.accept() #accepting connection from client
            arrival_time = time.time()
            try:
                log = Log()
                task = threading.Thread(target = self.request_handle, args = (client_socket, addr,arrival_time)) #creating thread for each client
                task.start()
            except Exception as e:
                print(f"Error: {e}")
                client_socket.close()
                log.write_log([client_socket,addr])
                
                break
        self.server_socket.close() 
        print("Server closed")
    def request_handle(self,clinet_socket,addr,time):
        log = Log()
        data = clinet_socket.recv(1024).decode() #receiving data from client
        http_obj = HTTP_Request(arrval_time= time)
        http_obj.parse(data)
        
        
        
        
        
