import socket
import threading
import json
import os
import logging
import time
from log import Log, BadRequest, UnSupportedMediaType
from myhttp import HTTP_Request, HTTP_Response, FileHandler, UnSupportedMediaType, HTTP_METHOD, Cache_Table_manager

class Server:
    def __init__(self):
        json_file = "config.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                config = json.load(f)
                self.host = config.get("host", "127.0.0.1")
                self.port = config.get("port", 42039)
                self.root = config.get("root", os.getcwd())
        else:
            print(f"Configuration file {json_file} not found. Using default values.")
            self.host = "127.0.0.1"
            self.port = 42039
            self.root = os.getcwd()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',handlers=[logging.StreamHandler()])
    def start(self):
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                client_socket.settimeout(60)
                logging.info(f"Client connected from {addr}")
                arrival_time = time.time()
                # Use threading to handle multiple clients
                try:
                    thread = threading.Thread(target=self.request_handle, args=(client_socket, addr, arrival_time))
                    thread.start()
                except SystemExit:
                    logging.info(f"Thread error: {threading.current_thread().name}")
                    client_socket.close()
        except Exception as e:
            logging.info(f"Server error: {e}")
        finally:
            self.server_socket.close()
            logging.info("Server closed")

    def request_handle(self, client_socket, addr, arrival_time):
        log = Log()
        while True:
            response = None
            data = b""
            # recv data
            try:
                logging.info(f"Handling request from {addr}")
                while True:
                    part = client_socket.recv(1024)
                    # logging.info(f"Receiving： {part.decode()}")
                    if not part or len(part)<1024:
                        logging.info(f"Received data from {addr}: {part},breaking")
                        
                        break
                    data += part
                data += part
                if not data:
                    logging.info(f"No data received from {addr}")
                    return
            except socket.timeout:
                logging.info(f"Timeout error from {addr}")
                response = HTTP_Response()
                response.set_status_code("BAD_REQUEST")
                response.connection = False
                response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
                log.write_log([str(addr), "Timeout error"],False)
            except Exception as e:
                logging.info(f"Receive error from {addr}: {e}")
                response = HTTP_Response()
                response.set_status_code("INTERNAL_SERVER_ERROR")
                response.body = "<html><body><h1>500 Internal Server Error</h1></body></html>"
                log.write_log([str(addr), f"Receive error: {e}"],True)
            # decode data
            if response is None:
                try:
                    data_str = data.decode()
                except Exception as e:
                    logging.info(f"Decode error from {addr}: {e}")
                    response = HTTP_Response()
                    response.set_status_code("BAD_REQUEST")
                    response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
                    log.write_log([str(addr), f"Decode error: {e}"],False)
            # parse http request
            if response is None:
                try:
                    logging.info(f"Received data from {addr}: {data_str}")
                    http_obj = HTTP_Request()
                    if  http_obj.parse(data_str) == None:
                        logging.info(f"Failed to parse HTTP request from {addr}")
                        response = HTTP_Response()
                        response.set_status_code("BAD_REQUEST")
                        response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
                        log.write_log([str(addr), "Parse error"],False)
                    log.write_log([str(addr), f"Parsed HTTP request: {str(http_obj)}"],False)
                except BadRequest as e:
                    logging.info(f"Bad request from {addr}: {e}")
                    response = HTTP_Response()
                    response.set_status_code("BAD_REQUEST")
                    response.body = f"<html><body><h1>400 Bad Request.{e.args}</h1></body></html>"
                    log.write_log([str(addr), f"Bad request: {e}"],False)
                except Exception as e:
                    logging.info(f"Parse error from {addr}: {e}")
                    response = HTTP_Response()
                    response.set_status_code("BAD_REQUEST")
                    response.body = "<html><body><h1>400 Bad Request,Unkonw except</h1></body></html>"
                    log.write_log([str(addr), f"Parse exception: {e}"],False)
            
            #logic
            if response is None:
                try:
                    if http_obj.method == HTTP_METHOD.GET or http_obj.method == HTTP_METHOD.HEAD:
                        fh = FileHandler(http_obj)
                        
                        fh.check(self.root)
                        response = HTTP_Response()
                        if hasattr(http_obj, "keep_alive") and http_obj.keep_alive == False:
                            response.set_connectoin(False)
                        elif hasattr(http_obj, "keep_alive") and http_obj.keep_alive == True:
                            response.set_connectoin(True)
                        if isinstance(fh.exception_msg, PermissionError):
                            response.set_status_code("FORBIDDEN")
                            response.body = "<html><body><h1>403 Forbidden</h1></body></html>"
                            log.write_log([str(addr), "Permission denied"],False)
                        elif isinstance(fh.exception_msg, FileNotFoundError):
                            response.set_status_code("NOT_FOUND")
                            response.body = "<html><body><h1>404 Not Found</h1></body></html>"
                            log.write_log([str(addr), "File not found"],False)
                        elif isinstance(fh.exception_msg, UnSupportedMediaType):
                            response.set_status_code("UNSUPPORTED_MEDIA_TYPE")
                            response.body = "<html><body><h1>415 Unsupported Media Type</h1></body></html>"
                            log.write_log([str(addr), "Unsupported media type"],False)
                        elif isinstance(fh.exception_msg, BadRequest):
                            response.set_status_code("BAD_REQUEST")
                            response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
                            log.write_log([str(addr), "Bad request"],False)
                        else:
                            if http_obj.last_modified_time is not None and int(fh.get_last_modified_time()) <= int(time.mktime(http_obj.last_modified_time)): # Not modified since
                                # print(f"Last:{time.mktime(http_obj.last_modified_time)}, fh:{fh.get_last_modified_time()}")
                                response.set_status_code("NOT_MODIFIED")
                                response.body = ""
                            else:
                                response.set_status_code("OK")
                                response.set_body(fh)
                                response.set_last_modified(fh.get_last_modified_time())
                        # else:
                        #     response = HTTP_Response()
                        #     response.set_status_code("NOT_FOUND")
                        #     response.body = "<html><body><h1>404 Not Found</h1></body></html>"
                    else:
                        response = HTTP_Response()
                        response.set_status_code("BAD_REQUEST")
                        response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
                except Exception as e:
                    logging.info(f"Business logic error from {addr}: {e}")
                    response = HTTP_Response()
                    response.set_status_code("INTERNAL_SERVER_ERROR")
                    response.body = "<html><body><h1>500 Internal Server Error</h1></body></html>"
                    log.write_log([str(addr), f"Business logic error: {e}"],True)
            #send response
            try:
                if response:
                    if http_obj is not None:
                        if http_obj.method == HTTP_METHOD.HEAD: #Head request, no body
                            response.body = ""
                            response.length = 0
                        response_head = response.gen_response_head()

                    response_msg = response_head.encode() + (response.body if isinstance(response.body, bytes) else response.body.encode())
                    client_socket.send(response_msg)
                    log.write_log([addr, f"Response sent: {response_head}"],False)
                    if isinstance(response.body, bytes):
                        logging.info(f"Binary file sent to{addr}:{response_head}")
                    else:
                        logging.info(f"Response sent to {addr}: {response_msg}")
            except Exception as e:
                logging.info(f"Send response error: {e}")
                log.write_log([str(addr), f"Send response error: {e}"],True)
            finally:
                print(f"response:{response.connection}")
                if response.connection == False:
                    client_socket.close()
                    logging.info(f"Connection with {addr} closed")
                    break
                client_socket.settimeout(60)
            

if __name__ == "__main__":
    server = Server()
    server.start()







