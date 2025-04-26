import socket
import threading
import json
import os
import time
from log import Log
from myhttp import HTTP_Request, HTTP_Response, FileHandler, HTTP_STATUS, HTTP_METHOD
class Server:
    def __init__(self):
        json_file = "config.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                config = json.load(f)
                self.host = config.get("host", "127.0.0.1")
                self.port = config.get("port", 8080)
        else:
            print(f"Configuration file {json_file} not found. Using default values.")
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
                break #break main thread if error
        self.server_socket.close() 
        print("Server closed")
    def request_handle(self,client_socket,addr,time):
        log = Log()
        try:
            data = client_socket.recv(1024).decode() #receiving data from client
            http_obj = HTTP_Request(arrval_time= time)
            http_obj.parse(data)
            if http_obj.method == HTTP_METHOD.GET:
                fh = FileHandler(http_obj) #init FileHandler
                if fh.exists():
                    response = HTTP_Response()
                    response.set_status_code("OK")
                    response.set_body(fh)
                    response.gen_response_head()
                else:
                    response = HTTP_Response()
                    response.set_status_code("NOT_FOUND")
                    response.set_body(fh)
                    response.gen_response_head()
        except Exception as e:
            print(f"Error: {e}")
            response = HTTP_Response()
            response.set_status_code("INTERNAL_SERVER_ERROR")
            response.set_body(None)
            response.gen_response_head()
            log.write_log([client_socket,addr])
        finally:
            client_socket.sendall(response.get_response().encode())
            client_socket.close()# no need to stop server, just send back response and write log.
   
if __name__ == "__main__":
    server = Server()
    server.start()    



        
        
        
        
