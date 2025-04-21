import socket
import os
class HTTP_STATUS:
    OK = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
class HTTP_Request:
    def __init__(self,arrval_time = None):
        self.method = None
        self.positon = None
        self.arrival_time = None
        self.type = None
        self.charset = None
    def parse(self,msg):
        lines = msg.split("\n")
        request_line = lines[0].split("/") # Method, URL, Version
        if(len(request_line) != 3):# request head format error
            return None
        elif(request_line[0].strip() == "GET"):
            self.method = "GET"
        elif(request_line[0].strip() == "HEAD"):
            self.method = "HEAD"
        else:
            return None
        self.positon = HTTP_Request.get_position(request_line[1]) #url:http://domain.com/path format
        self.type,self.charset = HTTP_Request.get_type(lines[1:]) #url:http://domain.com/path format
    def get_position(url):
        url_element = url.split("/")
        if(len(url_element) != 4):
            return None #url format lack of domain or path
        path = url_element[3]
        return path #相对路径
    def get_type(msg):
        for line in msg:
            if "Contetn_type" in line:
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
        request_head = f"{self.method}/{host}:{port}\{self.position}\Http/1.1\n"
        self.head = request_head
        return request_head
class HTTP_Response:
    def __init(self):
        self.status = None
        self.status_code = None
        self.body = None
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
        response_head = f"HTTP/1.1 {self.status_code} {self.status} {self.status}\n"
        self.head = response_head
        return response_head
    def set_body(self, http_obj:HTTP_Request):
        file_handler = FileHandler(http_obj)
        if http_obj.method == "GET":
            if file_handler.exists():
                self.body = file_handler.get_file_content()
                self.set_status_code("OK")
            else:
                self.set_status_code("NOT_FOUND")
        elif http_obj.method == "HEAD":
            if file_handler.exists():
                self.set_status_code("OK")
            else:
                self.set_status_code("NOT_FOUND")
        else:
            self.set_status_code("BAD_REQUEST")
        
class FileHandler:
    def __init__(self,http_obj:HTTP_Request):
        self.file_path = http_obj.position
        self.file_type = http_obj.type
        self.charset = http_obj.charset
    def exists(self):
        if os.path.exists(self.file_path):
            return True
        else:
            return False
    def get_file_content(self):
        if self.exists():
            if self.file_type == "text":
                with open(self.file_path, 'r',encoding=self.charset) as f:
                    content = f.read()
            elif self.file_type == "image":
                with open(self.file_path, 'rb',encoding=self.charset) as f:
                    content = f.read()
            return content
        else:
            return None

    