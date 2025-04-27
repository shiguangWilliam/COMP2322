import socket
import threading
import json
import os
import logging
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
                self.port = config.get("port", 42039)
        else:
            print(f"Configuration file {json_file} not found. Using default values.")
            self.host = "127.0.0.1"
            self.port = 42039
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',handlers=[logging.StreamHandler()])
    def start(self):
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                client_socket.settimeout(5)
                logging.info(f"Client connected from {addr}")
                arrival_time = time.time()
                # 使用线程处理每个客户端
                thread = threading.Thread(target=self.request_handle, args=(client_socket, addr, arrival_time))
                thread.start()
        except Exception as e:
            logging.info(f"Server error: {e}")
        finally:
            self.server_socket.close()
            logging.info("Server closed")

    def request_handle(self, client_socket, addr, arrival_time):
        log = Log()
        response = None
        data = b""
        # 1. 接收数据
        try:
            logging.info(f"Handling request from {addr}")
            while True:
                part = client_socket.recv(1024)
                logging.info(f"Receiving： {part.decode()}")
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
            response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
            log.write_log([str(addr), "Timeout error"])
        except Exception as e:
            logging.info(f"Receive error from {addr}: {e}")
            response = HTTP_Response()
            response.set_status_code("INTERNAL_SERVER_ERROR")
            response.body = "<html><body><h1>500 Internal Server Error</h1></body></html>"
            log.write_log([str(addr), f"Receive error: {e}"])
        # 2. 解码数据
        if response is None:
            try:
                data_str = data.decode()
            except Exception as e:
                logging.info(f"Decode error from {addr}: {e}")
                response = HTTP_Response()
                response.set_status_code("BAD_REQUEST")
                response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
                log.write_log([str(addr), f"Decode error: {e}"])
        # 3. 解析HTTP请求
        if response is None:
            try:
                logging.info(f"Received data from {addr}: {data_str}")
                http_obj = HTTP_Request()
                if  http_obj.parse(data_str) == None:
                    logging.info(f"Failed to parse HTTP request from {addr}")
                    response = HTTP_Response()
                    response.set_status_code("BAD_REQUEST")
                    response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
                    log.write_log([str(addr), "Parse error"])
            except Exception as e:
                logging.info(f"Parse error from {addr}: {e}")
                response = HTTP_Response()
                response.set_status_code("BAD_REQUEST")
                response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
                log.write_log([str(addr), f"Parse exception: {e}"])
        # 4. 业务逻辑处理
        if response is None:
            try:
                if http_obj.method == HTTP_METHOD.GET or http_obj.method == HTTP_METHOD.HEAD:
                    fh = FileHandler(http_obj)
                    if fh.exists():
                        response = HTTP_Response()
                        response.set_status_code("OK")
                        response.set_body(fh)
                    else:
                        response = HTTP_Response()
                        response.set_status_code("NOT_FOUND")
                        response.body = "<html><body><h1>404 Not Found</h1></body></html>"
                else:
                    response = HTTP_Response()
                    response.set_status_code("BAD_REQUEST")
                    response.body = "<html><body><h1>400 Bad Request</h1></body></html>"
            except Exception as e:
                logging.info(f"Business logic error from {addr}: {e}")
                response = HTTP_Response()
                response.set_status_code("INTERNAL_SERVER_ERROR")
                response.body = "<html><body><h1>500 Internal Server Error</h1></body></html>"
                log.write_log([str(addr), f"Business logic error: {e}"])
        # 5. 发送响应
        try:
            if response:
                logging.info(f"type:{type(response.gen_response_head())}")
                client_socket.send((response.gen_response_head() + (response.body if response.body else "")).encode())
        except Exception as e:
            logging.info(f"Send response error: {e}")
            log.write_log([str(addr), f"Send response error: {e}"])
        finally:
            client_socket.close()
            logging.info(f"Connection with {addr} closed")

if __name__ == "__main__":
    server = Server()
    server.start()







