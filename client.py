from myhttp import HTTP_Request, HTTP_Response, FileHandler, HTTP_STATUS, HTTP_METHOD
import socket
import os
import json
from log import Log
import logging

class CLI:
    def __init__(self):
        self.method = None
        self.is_list = False
    def get_input(self):
        while True:
            command = input("Enter your command (GET/HEAD): ") #GET/HEAD/List File_Path File_Type(text/image) Charset(optional,default urf-8)
            command_list = command.split(" ")
            http_obj = self.parse_command(command_list)
            if http_obj == None:
                continue
            client = Client()
            client.start(http_obj) #start client with request
        
    def parse_command(self,command_list):
        is_list = False
        if len(command_list) <=0:
            print("Invalid command. Please enter GET/HEAD List File_Path File_Type(b/t) Charset(optional,default urf-8)")
            return None
        if command_list[0] == "List":
            method = HTTP_METHOD.GET
            is_list = True # return list of files(name type charset)
        else:
            if len(command_list) < 3 or len(command_list) > 5:
                print("Invalid command. Please enter GET/HEAD List File_Path File_Type(b/t) Charset(optional,default urf-8)")
                return None
            if command_list[0] == "GET":
                method = HTTP_METHOD.GET
            elif command_list[0] == "HEAD":
                method = HTTP_METHOD.HEAD
            else:
                print("Invalid command. Please enter GET or HEAD.")
                return None
        position = command_list[1]
        file_type = command_list[2]
        charset = "utf-8" #default charset
        if len(command_list) == 4:
            charset = command_list[3]
        if is_list:
            file_type = "list"
            position = None
        http_obj = HTTP_Request()
        http_obj.set_method(method)
        http_obj.set_position(position)
        http_obj.set_type(file_type, charset)
        return http_obj
        


class Client:
    def __init__(self):
        json_file = "config.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                config = json.load(f)
                self.host = config.get("host", "127.0.0.1") #sever host
                self.port = config.get("port", 42039) #sever port
        else:
            self.host = "127.0.0.1" #sever host
            self.port = 42039 #sever port
            print(f"Configuration file {json_file} not found. Using default values.")
    def start(self,http_obj:HTTP_Request):
        log = Log()
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        request = http_obj.gen_request(self.host, self.port) #generate request head
        try:
            clientSocket.connect((self.host, self.port)) #connect to server
            print(f"Connected to server {self.host}:{self.port}")
            clientSocket.send(request.encode()) #send request to server
            print(f"Request sent: {request}")
            data = b""
            while True:
                part = clientSocket.recv(1024)
                logging.info(f"Received data from server: {part}")
                if not part:
                    break
                data += part
            response = data.decode()
            print(f"Response from server: {response}")
        except Exception as e:
            print(f"Error: {e}")
            log.write_log([clientSocket, str(e) ])
        finally:
            clientSocket.close()
            print("Connection closed") 

if __name__ == "__main__":
    cli = CLI()
    cli.get_input()
