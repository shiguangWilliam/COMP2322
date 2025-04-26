import socket
import os
class HTTP_STATUS:
    OK = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
class HTTP_METHOD:
    GET = "GET"
    HEAD = "HEAD"
class HTTP_Request:
    def __init__(self,arrval_time = None):
        self.method = None
        self.position = None
        self.arrival_time = None
        self.type = None
        self.charset = None
    def parse(self,msg):
        lines = msg.split("\n")
        request_line = lines[0].split(" ") # Method pos Version
        if(len(request_line) != 3):# request head format error
            return None
        elif(request_line[0].strip() == "GET"):
            self.method = HTTP_METHOD.GET
        elif(request_line[0].strip() == "HEAD"):
            self.method = HTTP_METHOD.HEAD
        else:
            return None
        self.position = request_line[1] 
        self.type,self.charset = HTTP_Request.get_type(lines[1:])
        if self.type == None:
            return None
    
    def get_type(msg):
        file_type = None
        charset = "utf-8" #default charset
        for line in msg:
            if "Content_type" in line:
                file_type = line.split(":")[1].strip()
            elif "Charset" in line:
                charset = line.split(":")[1].strip()
        return file_type, charset #file type and charset
    def set_method(self, method):
        self.method = method
    def set_position(self, position):
        self.position = position
    def set_type(self,type, charset):
        self.type = type
        self.charset = charset
    def gen_request_head(self,host, port):
        request_head = f"{self.method} {self.position} Http/1.1\n"
        self.head = request_head
        return request_head
    
class FileHandler:
    def __init__(self,http_obj:HTTP_Request):
        self.file_path = http_obj.position
        self.file_type = http_obj.type
        self.charset = http_obj.charset
    def exists(self):
        return os.path.exists(self.file_path) and os.path.isfile(self.file_path) # check if file exists and not dir
    def get_file_content(self):
        if not self.exists():
            return None
        try:
            if self.file_type == "text":
                with open(self.file_path, 'r',encoding=self.charset) as f:
                    content = f.read()
                    content - content.encode(self.charset) # encode to bytes
            elif self.file_type == "image":
                with open(self.file_path, 'rb') as f:
                    content = f.read()
            return content
        except Exception as e:
            raise Exception("File Read Error") # file read error, will be handle outside in server.py

class HTTP_Response:
    def __init__(self):
        self.status = None
        self.status_code = None
        self.body = None
        self.content_type = None
        self.headers = None
    def set_status_code(self, status): # map talbe for status code
        if status == "OK":
            self.status_code = HTTP_STATUS.OK
            self.status = status
        elif status == "BAD_REQUEST":
            self.status_code = HTTP_STATUS.BAD_REQUEST
            self.status = status
        elif status == "NOT_FOUND":
            self.status_code = HTTP_STATUS.NOT_FOUND
            self.status = status
        elif status == "INTERNAL_SERVER_ERROR":
            self.status_code = HTTP_STATUS.INTERNAL_SERVER_ERROR
            self.status = status
            raise Exception("Internal Server Error")
        else:
            raise Exception("Unknown Status Code")
    def gen_response_head(self):
        response_head_line = f"HTTP/1.1 {self.status_code} {self.status} {self.status}\n"
        response_head={"Content-Type":str(self.content_type),
                       "Content-Length":str(len(self.body))}
        head_str = "\r\n".join(f"{key}: {value}" for key, value in response_head.items())
        self.headers = response_head + "\r\n" + head_str + "\r\n"
        response_head = self.headers
        return response_head
    def set_body(self, file_handler:FileHandler):
        if file_handler == None or file_handler.exists() == False:
            self.body = None
        else:
            self.content_type = file_handler.file_type
            self.body = file_handler.get_file_content()
        
        

    