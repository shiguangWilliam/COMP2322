from myhttp import HTTP_Request, HTTP_Response, FileHandler, FileTypeManager, HTTP_METHOD,Cache_Table_manager
import socket
import os
import json
from log import Log
import logging
import time
import threading

class CLI:
    def __init__(self):
        self.timeout = False

    def get_input_with_timeout(self, prompt, timeout=60):
        """Get user input with a timeout."""
        user_input = [None]  # Use a mutable object to store input

        def input_thread():
            user_input[0] = input(prompt)

        thread = threading.Thread(target=input_thread)
        thread.daemon = True
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            self.timeout = True
            print("\nInput timed out!")
            return None
        return user_input[0]

    def get_input(self):
        """Get user input with timeout handling."""
        command = self.get_input_with_timeout("Enter your command (GET/HEAD): ", timeout=60)
        if command is None:
            print("No input received within the timeout period.")
            return None
        command_list = command.split(" ")
        return command_list
        
    def parse_command(self, command_list):
        if len(command_list) <= 0:
            print("Invalid command. Please enter GET/HEAD File_Path File_Type(b/t) Connection(optional,default keep-alive. Can be set to close)")
            return None
        if len(command_list) < 3 or len(command_list) > 6:
            print("Invalid command. Please enter GET/HEAD File_Path File_Type(b/t) Connection(optional,default keep-alive. Can be set to close)")
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
        # http_obj.set_last_modified_time(timestamp=os.path.getmtime(position) if os.path.exists(position) else 0)# set last modified time
        http_obj.set_connection("keep-alive" if connection==None else connection) # set connection default keep-alive
        return http_obj


class Client:
    def __init__(self):
        json_file = "config.json"
        self.file_path = None
        self.cache_table = None
        self.cahce_folder = None
        self.connect = True
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
            self.cache_manager = Cache_Table_manager(self.cache_table,self.cache_folder) #cache table manager
        except FileNotFoundError:
            print(f"Cache table file {self.cache_table} not found.")
            self.log.write_log([self.host, "Cache table file not found"],True)
    def start(self):
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            clientSocket.connect((self.host, self.port))  # connect to server
        except Exception as e:
            print(f"Error: {e}")
            self.log.write_log([self.host, str(e)],True)
            return        
        while True:
            response = None
            if self.connect == False:
                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                clientSocket.send(b"")
            except ConnectionResetError as e:
                print(f"Connection reset by server {self.host}:{self.port}")
                self.log.write_log([clientSocket, str(e)],False)
                clientSocket.close()
                break
            except socket.error as e:
                clientSocket.connect((self.host, self.port))  # reconnect to server
                print(f"Reconnected to server {self.host}:{self.port}")
            cli = CLI()
            self.cache_manager.reload() #update
            while True:
                command = cli.get_input() #get command from user with timeout
                if cli.timeout is True:
                    # print("Exiting due to no input.")
                    clientSocket.close()
                    self.connect = False
                    cli.timeout = False
                    continue
                http_obj = cli.parse_command(command) #parse command
                if http_obj != None:
                    break
            
            if self.connect == False:
                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                clientSocket.connect((self.host, self.port))  # reconnect to server
            self.file_path = http_obj.position  # file path
            # print(f"client table:{self.cache_manager.table}")
            info = self.cache_manager.check_cache(http_obj.position)  # check cache table
            # print(info)
            if info != None:
                http_obj.set_last_modified_time(cache_table_manager=self.cache_manager)   # get cache data
            else:
                http_obj.set_last_modified_time() #No last modified time
            request = http_obj.gen_request(self.host, self.port)  # generate request head
            try:
                print(f"Connected to server {self.host}:{self.port}")
                
                
                clientSocket.send(request.encode())  # send serialized request to server
                print(f"Request sent: {request}")
                
                data = b""
                while True:
                    part = clientSocket.recv(1024)
                    if not part or len(part)<1024:
                        break
                    data += part
                data += part
                ftype = FileTypeManager()
                #process response data,especially for image data
                datalist = data.split(b"\r\n")
                
                head_line = datalist[:5] #header line
                # print(head_line)
                head = ""
                for i in range(5):
                    head += datalist[i].decode() + "\r\n"
                
                response = HTTP_Response()
                response.parse(head)  # parse response data
                # header = header.decode()
                body = data[len(data)-int(response.length):]  # get body data,skip \r\n
                print(f"Received data from server: {head_line}")
                
                #set body
                if response.status_code == 200:
                    if ftype.parse_file_type(response.content_type) == "image":
                        response.body = body
                    else:
                        response.body = body.decode()
                
                print(f"Response from server: {response.status_code}, {response.status}")
                self.parse_handle(response, http_obj)  # parse response data
            except Exception as e:
                print(f"Error: {e}")
                self.log.write_log([clientSocket, str(e)],False)
            finally:
                while True:
                    next_step = input("Do you want to continue? (y/n): ")
                    if next_step.lower() in ["y", "n"]:
                        break
                    else:
                        print("Invalid input")
                if next_step.lower() == "n":
                    clientSocket.close()
                    print("Connection closed")
                    with open(self.cache_table, 'w') as f: #empty cache table
                        pass
                    def remove_cache_files(folder):
                        for root, dirs, files in os.walk(folder):
                            for file in files:
                                if file == "cache_table.json":
                                    continue
                                file_path = os.path.join(root, file)
                                os.remove(file_path)
                    remove_cache_files(self.cache_folder) #empty cache folder
                    break
                elif next_step.lower() == "y": 
                    if response is None:
                        continue
                    if response.connection == "close":
                        clientSocket.close()
                        self.connect = False
                        print("Connection closed")
                else:
                    print("Invalid input")
                    
    def parse_handle(self,i_response:HTTP_Response, http_obj:HTTP_Request):
        resposne = None
        response = i_response
        # print(response.status_code == "200")
        if response.status_code == 200:
            if http_obj.method == HTTP_METHOD.GET:
                self.cache_manager.update_cache(http_obj.position, response.last_modified)  # update cache table
                ftype = FileTypeManager()
                base_type = ftype.parse_file_type(response.content_type)  # parse file type
                # print(f"File type: {base_type}")
                io_mode = "w"
                os.makedirs(os.path.dirname(http_obj.position), exist_ok=True)  # create directory if not exist
                if base_type == "image":
                    io_mode = "wb"
                with open(http_obj.position, io_mode) as f:
                    f.write(response.body)
                self.cache_manager.copy_cache(http_obj.position,os.path.join(self.cache_folder,os.path.dirname(http_obj.position))) #copy file to cache folder
                print(f"File {http_obj.position} saved to cache folder")
        elif response.status_code == 304:
            print(f"File {http_obj.position} has not been modified")
            # print(f"Source{os.path.join(self.cache_folder,os.path.dirname(http_obj.position))},dist{http_obj.position}")
            info = self.cache_manager.check_cache(http_obj.position)  # check cache table
            self.cache_manager.copy_cache(info[1],os.path.dirname(http_obj.position)) #copy file from cache folder
        else:
            print(f"Response from server: {response.status_code}, {response.status}")
            if response.body is not None:
                # print(f"Response body: {response.body}")
                with open("response.html","w") as f:
                    f.write(response.body)
if __name__ == "__main__":
    client = Client()
    client.start()
