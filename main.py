import argparse
import json
import os
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import uuid,cgi
from control import diffControl

class RequestHandler(SimpleHTTPRequestHandler):
    API_ROUTES = {
        '/api/compare': {'POST', 'GET', 'OPTIONS'}  # 使用集合存储允许的方法
    }

    def do_GET(self):
        if self.path.startswith('/api'):
            self.handle_api_route('GET')
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api'):
            self.handle_api_route('POST')
        else:
            self.send_error(404, "Not Found")

    def handle_api_route(self, method):
        # 标准化路径处理
        parsed_path = urlparse(self.path)
        route = parsed_path.path.rstrip('/')  # 统一处理路径格式

        if route not in self.API_ROUTES:
            self.send_error(404, f"Endpoint {route} not found")
            return

        allowed_methods = self.API_ROUTES[route]
        if method not in allowed_methods:
            self.send_error(405, f"Method {method} not allowed")
            return

        # 构造处理函数名称
        handler_name = f'handle_{method.lower()}_{route[1:].replace("/", "_")}'
        handler = getattr(self, handler_name, None)
        
        if not handler:
            self.send_error(500, f"Handler {handler_name} not implemented")
            return

        # 处理请求
        handler()

    # 覆盖默认的send_error方法
    def send_error(self, code, message=None, details=None):
        self.log_error("Error code %d: %s", code, message)
        response = {
            "status": "error",
            "code": code,
            "message": message or self.responses[code][0],
            "details": details or ""
        }
        
        self.send_response(code)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def handle_post_api_compare(self):
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )

            # 获取文件
            file1 = form['file1']
            file2 = form['file2']

            if not (file1.filename and file2.filename):
                self.send_error(400, "Missing required files", {"required_fields": ["file1", "file2"]})
                return

            # 处理文件保存
            save_dir = './file_input'
            os.makedirs(save_dir, exist_ok=True)
            
            def save_file(file_item):
                # 获取原始文件扩展名
                original_filename = os.path.basename(file_item.filename)
                _, ext = os.path.splitext(original_filename)

                # 生成唯一文件名
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                save_path = save_dir + '/' + unique_filename

                # 保存文件
                with open(save_path, 'wb') as f:
                    f.write(file_item.file.read())

                return save_path  # 返回完整保存路径
            
            file1_name = os.path.basename(file1.filename)
            file2_name = os.path.basename(file2.filename)
            _, ext1 = os.path.splitext(file1_name)
            _, ext2 = os.path.splitext(file2_name)
            if ext1.lower() != ext2.lower():
                self.send_error(400, "Different file types cannot be compared", {"required_fields": ["file1", "file2"]})
                return
            file1_path = save_file(file1)
            file2_path = save_file(file2)
            # 调用模块进行比较
            state, diff_output_url = diffControl(file1_path, file2_path,file1_name,file2_name,ext1)
            if state == 'no':
                self.send_error(400, diff_output_url, {"required_fields": ["file1", "file2"]})
                return
            # 发送响应
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'success',
                'diff': diff_output_url
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON format")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def handle_get_api_compare(self, data):
        try:
            # 发送响应
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'success',
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON format")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")


    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')

    def do_OPTIONS(self):
        parsed_path = urlparse(self.path)
        route = parsed_path.path.rstrip('/')
        
        if route in self.API_ROUTES:
            self.send_response(204)
            self._set_cors_headers()
            self.send_header('Allow', ', '.join(self.API_ROUTES[route]))
            self.end_headers()
        else:
            self.send_error(404, "Not Found")

def run_server(port=9010, directory='.'):
    # 切换到指定目录
    try:
        os.chdir(os.path.abspath(directory))
    except FileNotFoundError:
        print(f"错误：目录 '{directory}' 不存在")
        sys.exit(1)
    # 创建服务器实例
    server_address = ('', port)
    # handler_class = SimpleHTTPRequestHandler
    # httpd = HTTPServer(server_address, handler_class)
    httpd = ThreadingHTTPServer(server_address, RequestHandler)
    
    # 获取实际使用的端口（当port=0时系统会自动分配）
    actual_port = httpd.socket.getsockname()[1]
    
    print(f"在端口 {actual_port} 上启动服务，服务目录: {os.getcwd()}")
    print(f"访问地址: http://localhost:{actual_port}/public/index.html")
    print("按 Ctrl+C 停止服务")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == '__main__':
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='静态文件HTTP服务器')
    parser.add_argument('-p', '--port', type=int, default=9010,
                        help='指定端口号（默认：9010）')
    parser.add_argument('-d', '--directory', default='.',
                        help='指定服务目录（默认：当前目录）')
    
    args = parser.parse_args()

    # 运行服务器
    run_server(args.port, args.directory)