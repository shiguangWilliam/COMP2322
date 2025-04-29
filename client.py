from myhttp import HTTP_Request, HTTP_Response, FileHandler, HTTP_STATUS, HTTP_METHOD,Cache_Table_manager
import socket
import os
import json
from log import Log
import logging
import time

class CLI:
    def __init__(self):
        self.method = None
    def get_input(self):
        while True:
            command = input("Enter your command (GET/HEAD): ") #GET/HEAD File_Path File_Type(text/image) Connection)
            command_list = command.split(" ")
            http_obj = self.parse_command(command_list)
            if http_obj == None:
                continue
            client = Client()
            client.start(http_obj) #start client with request
        
    def parse_command(self, command_list):
        if len(command_list) <= 0:
            print("Invalid command. Please enter GET/HEAD File_Path File_Type(b/t) Charset(optional,default urf-8)")
            return None
        if len(command_list) < 3 or len(command_list) > 6:
            print("Invalid command. Please enter GET/HEAD File_Path File_Type(b/t) Charset(optional,default urf-8)")
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
        charset = "utf-8"  # default charset
        connection = None
        if len(command_list) == 4:
            connection = command_list[3]
        http_obj = HTTP_Request()
        http_obj.set_method(method)
        http_obj.set_position(position)
        http_obj.set_type(file_type, charset)
        http_obj.set_last_modified_time(timestamp=os.path.getmtime(position) if os.path.exists(position) else 0)# set last modified time
        http_obj.set_connection("keep-alive" if connection==None else connection) # set connection default keep-alive
        return http_obj


class Client:
    def __init__(self):
        json_file = "config.json"
        self.file_path = None
        self.cache_table = None
        self.cahce_folder = None
        self.log = Log()
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                config = json.load(f)
                self.host = config.get("host", "127.0.0.1") #sever host
                self.port = config.get("port", 42039) #sever port
                self.cache_table = config.get("cache_table", "./cache/cache.json") #cache file
                self.cache_folder = config.get("cache_folder", "./cache") #cache folder
        else:
            self.host = "127.0.0.1" #sever host
            self.port = 42039 #sever port
            self.cache_table = "./cache/cache.json"
            self.cache_folder = "./cache"
            print(f"Configuration file {json_file} not found. Using default values.")
        try:
            self.cache_manager = Cache_Table_manager(self.cache_table) #cache table manager
        except FileNotFoundError:
            print(f"Cache table file {self.cache_table} not found.")
            self.log.write_log([self.host, "Cache table file not found"])
    def start(self, http_obj: HTTP_Request):
        self.file_path = http_obj.position  # file path
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        request = http_obj.gen_request(self.host, self.port)  # generate request head
        try:
            clientSocket.connect((self.host, self.port))  # connect to server
            print(f"Connected to server {self.host}:{self.port}")
            
            
            clientSocket.send(request.encode())  # send serialized request to server
            print(f"Request sent: {request}")
            
            data = b""
            while True:
                part = clientSocket.recv(1024)
                if not part:
                    break
                data += part
            
            # 反序列化响应数据
            response_data = json.loads(data.decode())
            response = HTTP_Response()
            response.status_code = response_data.get("status_code")
            response.status = response_data.get("status")
            response.content_type = response_data.get("content_type")
            response.body = response_data.get("body").encode() if response_data.get("body") else None
            
            print(f"Response from server: {response}")
        except Exception as e:
            print(f"Error: {e}")
            self.log.write_log([clientSocket, str(e)])
        finally:
            clientSocket.close()
            print("Connection closed")

if __name__ == "__main__":
    cli = CLI()
    cli.get_input()
