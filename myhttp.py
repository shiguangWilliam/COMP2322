import socket
import os
class HTTP_STATUS:
    OK = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    FORBIDDEN = 403
    NOT_MODIFIED = 304
    UNSUPPORTED_MEDIA_TYPE = 415
class HTTP_METHOD:
    GET = "GET"
    HEAD = "HEAD"
class UnSupportedMediaType(Exception):...
class FileTypeManager:
    def __init__(self):
        self.supported_types = {
            "txt":"text",
            "html":"text",
            "css":"text",
            "js":"text",
            "json":"text",
            "jpg":"image",
            "jpeg":"image",
            "png":"image",
        }
         
    def get_file_type(self, file_path):
        if not os.path.exists(file_path):
            return None
        file_name, file_extension = os.path.splitext(file_path)
        file_extension = file_extension[1:]
        if file_extension in self.supported_types:
            return f"{self.supported_types.get(file_extension)}/{file_extension}"
        else:
            return None # 415 Unsupported Media Type
    def check_file_type(self,file_path):
        file_name, file_extension = os.path.splitext(file_path)
        file_extension = file_extension[1:]
        if file_extension in self.supported_types:
            return True
        else:
            return False
class HTTP_Request:
    def __init__(self):
        self.method = None
        self.position = None
        self.type = None
        self.charset = None
    def __str__(self):
        return f"Method: {self.method}, Position: {self.position}, Type: {self.type}, Charset: {self.charset}"
    def parse(self,msg):
        lines = msg.split("\r\n")
        if(len(lines)<2):
            return None
        
        request_line = lines[0].split(" ") # Method pos Version
        print(f"Request line: {request_line[0].strip()}")
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
        return self
    
    def get_type(msg):
        file_type = None
        charset = "utf-8" #default charset
        for line in msg:
            if "Content-Type" in line:
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
    def gen_request(self,host, port):
        request_head = f"{self.method} {self.position} Http/1.1\r\n"
        request_body = {"Content-Type":self.type,
                           "Charset":self.charset}
        request_head += "\r\n".join(f"{key}: {value}" for key, value in request_body.items())
        return request_head
    
class FileHandler:
    def __init__(self,http_obj:HTTP_Request):
        self.file_path = http_obj.position
        self.file_type = http_obj.type
        self.charset = http_obj.charset
        self.exception_flag = False
        self.exception_msg = None
        self.file_type_manager = FileTypeManager()
    def exists(self):
        return os.path.exists(self.file_path) and os.path.isfile(self.file_path) # check if file exists and not dir
    def get_file_content(self):
        if not self.exists():
            return None
        # file_type_manager = FiletTypeManager()
        if self.file_type_manager.check_file_type(self.file_path) == False:
            self.exception_flag = True
            self.exception_msg = UnSupportedMediaType()
            return None
        try:
            if self.file_type == "text":
                with open(self.file_path, 'r', encoding=self.charset) as f:
                    content = f.read()
            elif self.file_type == "image":
                with open(self.file_path, 'rb') as f:
                    content = f.read()
            return content
        except FileNotFoundError:
            self.exception_flag = True
            self.exception_msg = FileNotFoundError()
            return None
        except PermissionError:
            self.exception_flag = True
            self.exception_msg = PermissionError()
            return None
        except Exception as e:
            self.exception_flag = True
            self.exception_msg = e
            return None
            # raise Exception("File Read Error") # file read error, will be handle outside in server.py
    def get_last_modified_time(self):
        if not self.exists():
            return None
        try:
            last_modified_time = os.path.getmtime(self.file_path)
            return last_modified_time
        except Exception as e:
            self.exception_flag = True
            self.exception_msg = e
            return None
            # raise Exception("File Read Error")
class HTTP_Response:
    STATUS_MAP = {
        "OK": HTTP_STATUS.OK,
        "BAD_REQUEST": HTTP_STATUS.BAD_REQUEST,
        "NOT_FOUND": HTTP_STATUS.NOT_FOUND,
        "INTERNAL_SERVER_ERROR": HTTP_STATUS.INTERNAL_SERVER_ERROR,
        "FORBIDDEN": HTTP_STATUS.FORBIDDEN,
        "NOT_MODIFIED": HTTP_STATUS.NOT_MODIFIED,
        "UNSUPPORTED_MEDIA_TYPE": HTTP_STATUS.UNSUPPORTED_MEDIA_TYPE,
    }
    def __init__(self):
        self.status = None
        self.status_code = None
        self.body = None
        self.content_type = None
        self.headers = None
        
    def set_status_code(self, status): # map talbe for status code
        if status in HTTP_Response.STATUS_MAP:
            self.status_code = HTTP_Response.STATUS_MAP[status]
            self.status = status
        else:
            raise Exception("Unknown Status Code")
    def gen_response_head(self):
        response_head_line = f"HTTP/1.1 {self.status_code} {self.status}\n"
        response_head={"Content-Type":str(self.content_type),
                       "Content-Length":str(len(self.body))}
        head_str = "\r\n".join(f"{key}: {value}" for key, value in response_head.items())
        self.headers = response_head_line + "\r\n" + head_str + "\r\n"
        # response_head = self.headers
        return self.headers # response head
    def set_body(self, file_handler:FileHandler):
        if file_handler == None or file_handler.exists() == False:
            self.body = None
            self.status_code = HTTP_STATUS.NOT_FOUND
            self.status = "NOT_FOUND"
        else:
            self.content_type = file_handler.file_type_manager.get_file_type(self.body)
            content = file_handler.get_file_content()
            if content != None:
                self.body = content
            elif file_handler.exception_flag == True:
                self.body = None
                raise file_handler.exception_msg
    def get_response(self):
        if self.body is None:
            return self.headers
        return self.headers + self.body
    def parse(self,msg):
        lines = msg.split("\r\n")
        header = lines[0].split(" ") # Method pos Version
        self.status_code = header[1]
        self.status = header[2]
        



