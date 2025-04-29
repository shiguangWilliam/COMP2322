import socket
import os
import time
import json
import shutil
from log import UnSupportedMediaType,BadRequest
import re
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
    def parse_file_type(self,file_type:str):
        s_type = re.split(r"/|\\",file_type)[1] 
        print(f"stype:{s_type}")
        return self.supported_types.get(s_type) # text/image

class Cache_Table_manager:
    def __init__(self,cache_table,cache_folder):
        self.cache_table_pos = cache_table
        self.cache_folder = cache_folder
        if os.path.exists(self.cache_table_pos) == False:
            raise FileNotFoundError("Cache table not found")
        with open(self.cache_table_pos, 'r') as f:
            print(f.read())
            f.seek(0) #test only
            if f.read() =="":
                self.table = {}
            else:
                f.seek(0) # init seek
                self.table = json.load(f)
                print(self.table)
    def check_cache(self,file_path):
        print(f"table{self.table}")
        cache = self.table.get(file_path)
        if cache is None:
            return None
        last_modified_time = cache.get("last_modified_time")
        cache_file_path = cache.get("file_path")
        return (last_modified_time, cache_file_path)
    def update_cache(self,file_path, last_modified_time):
        self.table[file_path] = {
            "last_modified_time": last_modified_time,
            "file_path": os.path.join(self.cache_folder, file_path)
        }
        with open(self.cache_table_pos, 'w') as f:
            json.dump(self.to_dict(self.table), f)
    def copy_cache(self,source,dist):
        if os.path.exists(source) == False:
            return False
        if os.path.exists(dist) == False:
            os.makedirs(dist)
        shutil.copy(source,dist)
    def to_dict(self,table):
        print(dict(table))
        return dict(table)
    def reload(self):
        with open(self.cache_table_pos, 'r') as f:
            if f.read() =="":
                self.table = {}
                return
            f.seek(0) #set to begin
            self.table = json.load(f)
        print(f"Reloaded cache table: {self.table}")
    
        
 
class HTTP_Request:
    def __init__(self):
        self.method = None
        self.position = None
        self.type = None
        self.charset = None
        self.parse_complete = False
    def __str__(self):
        return f"Method: {self.method}, Position: {self.position}, Type: {self.type}, Charset: {self.charset}"
    def parse(self,msg):
        lines = msg.split("\r\n")
        if(len(lines)<2):
            return None
        
        request_line = lines[0].split(" ") # Method pos Version
        print(f"Request line: {request_line[0].strip()}")
        if(len(request_line) != 3):# request head format error
            raise(BadRequest("Request line format error"))
        elif(request_line[0].strip() == "GET"):
            self.method = HTTP_METHOD.GET
        elif(request_line[0].strip() == "HEAD"):
            self.method = HTTP_METHOD.HEAD
        else:
            raise(BadRequest("Request method error"))
        
        self.position = request_line[1] 
        self.type,self.charset = HTTP_Request.get_type(lines[1:])
        
        self.last_modified_time = HTTP_Request.get_last_modified_time(lines[1:])
        self.keep_alive = HTTP_Request.get_keep_alive(lines[1:])

        self.parse_complete = True #set complete flag
        return self
    
    def get_keep_alive(msg):
        keep_alive = True
        for line in msg:
            if "Connection" in line:
                if "close" in line:
                    keep_alive = False
                return keep_alive
        raise(BadRequest("Request Connection error"))
                
        return keep_alive
    def parse_http_data(http_data:str):
        try:
            ts_tuple = time.strptime(http_data, "%Y-%m-%d %H-%M-%S")
        except ValueError:
            raise(BadRequest("Request last modified time format error")) #Bad request
        else:
            return ts_tuple
    def get_last_modified_time(msg):
        last_modified_time = None
        for line in msg:
            if "If-Modified-Since" in line:
                last_modified_time = line.split(":")[1].strip()
                if last_modified_time == "":
                    return None
                print(f"Last modified time: {last_modified_time}")
                last_modified_time = HTTP_Request.parse_http_data(last_modified_time)
                return last_modified_time
        raise(BadRequest("Request last modified time error"))
    def get_type(msg):
        file_type = None
        charset = "utf-8" #default charset
        flag_set = [False, False] # file type and charset flag
        for line in msg:
            if "Content-Type" in line:
                file_type = line.split(":")[1].strip()
                flag_set[0] = True  #find type
            elif "Charset" in line:
                charset = line.split(":")[1].strip()
                flag_set[1] = True #find charset
        if all(flag_set):
            return file_type, charset #No matter has content or empty.
        raise (BadRequest("Request type error")) #Request must contain content type and charset
    def set_method(self, method):
        self.method = method
    def set_position(self, position):
        self.position = position
    def set_type(self, type, charset):
        self.type = FileTypeManager().get_file_type(type)
        if self.type is None:
            self.type = type  # set to request type (will be handled by server)
        self.charset = charset
    def set_last_modified_time(self,cache_table_manager:Cache_Table_manager=None):
        if cache_table_manager == None:
            self.last_modified_time = None
            return
        info_list = cache_table_manager.check_cache(self.position)
        if info_list == None:
            self.last_modified_time = ""
        else:
            self.last_modified_time = info_list[0]
    def set_connection(self, connection):
        if connection == "keep-alive":
            self.keep_alive = True
        else:
            self.keep_alive = False
    def gen_request(self, host, port):
        if not all(hasattr(self,attr) for attr in ['method', 'position', 'type', 'charset','last_modified_time', 'keep_alive']):
            raise ValueError("All HTTP_Request attributes must be set before generating the request.")
        
        request_head = f"{self.method} {self.position} HTTP/1.1\r\n"
        request_body = {
            "Content-Type": self.type,
            "Charset": self.charset,
            "If-Modified-Since": self.last_modified_time if self.last_modified_time else "",
            "Connection": "keep-alive" if self.keep_alive else "close"
        }
        request_head += "\r\n".join(f"{key}: {value}" for key, value in request_body.items()) + "\r\n\r\n"
        return request_head
    
class FileHandler:
    def __init__(self,http_obj:HTTP_Request):
        self.file_path = http_obj.position
        self.file_type = http_obj.type
        self.charset = http_obj.charset
        self.exception_flag = False
        self.exception_msg = None
        self.file_type_manager = FileTypeManager()
    def check(self,root):
        abs_path = os.path.abspath(self.file_path)
        root_path = os.path.abspath(root)
        if not abs_path.startswith(root_path):
            self.exception_flag = True
            self.exception_msg = PermissionError() #403
            return False
        if os.path.exists(self.file_path) == False:
            self.exception_flag = True
            self.exception_msg = FileNotFoundError() #404
            return False
        if self.file_type_manager.check_file_type(self.file_path) == False:
            self.exception_flag = True
            self.exception_msg = UnSupportedMediaType() #415
            return False
        return True
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
        self.connection = True # default keep-alive
        self.last_modified = None
        
    def set_status_code(self, status): # map talbe for status code
        if status in HTTP_Response.STATUS_MAP:
            self.status_code = HTTP_Response.STATUS_MAP[status]
            self.status = status
        else:
            raise Exception("Unknown Status Code")
    def gen_response_head(self):
        response_head_line = f"HTTP/1.1 {self.status_code} {self.status}"
        response_head={"Content-Type":str(self.content_type),
                       "Content-Length":str(len(self.body)),
                       "Last-Modified":time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(self.last_modified)) if self.last_modified else "",
                       "Connection":"keep-alive" if self.connection else "close",}
        head_str = "\r\n".join(f"{key}: {value}" for key, value in response_head.items())
        self.headers = response_head_line + "\r\n" + head_str + "\r\n"
        # response_head = self.headers
        return self.headers # response head
    def set_body(self, file_handler: FileHandler):
        if file_handler is None or not file_handler.exists():
            self.body = None
            self.status_code = HTTP_STATUS.NOT_FOUND
            self.status = "NOT_FOUND"
        else:
            self.content_type = file_handler.file_type_manager.get_file_type(file_handler.file_path)
            content = file_handler.get_file_content()
            if content is not None:
                self.body = content
            elif file_handler.exception_flag:
                self.body = None
                raise file_handler.exception_msg
    def set_connectoin(self, connection):
        if connection:
            self.connection = True
        else:
            self.connection = False
    def set_last_modified(self, last_modified_time):
        self.last_modified = last_modified_time
    def get_response(self):
        if self.body is None:
            return self.headers
        return self.headers.encode() + self.body if isinstance(self.body, bytes) else self.headers + self.body
    def parse(self,msg):
        lines = msg.split("\r\n")
        for line in lines[:]: # iterate a copy of the list to avoid modifying it while iterating
            if line == "":
                lines.remove(line) # remove empty line
        if len(lines) < 4 or len(lines)>5:
            raise Exception("Invalid Response")
        header = lines[0].split(" ") # Method pos Version
        self.status_code = int(header[1])
        self.status = header[2]
        self.content_type = lines[1].split(":")[1].strip()
        self.length = lines[2].split(":")[1].strip()
        self.last_modified = lines[3].split(":")[1].strip()
        self.connection = lines[4].split(":")[1].strip()
        # self.body = lines[5]
        




