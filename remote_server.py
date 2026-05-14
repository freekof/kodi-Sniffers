import http.server
import socketserver
import threading
import socket
import urllib.parse

# 全局变量用于存储接收到的 URL
received_url = None
server_instance = None

class RemoteInputHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>KODI Video Sniffer Remote Input</title>
                <style>
                    body { font-family: sans-serif; text-align: center; padding: 20px; background-color: #f0f0f0; }
                    input[type="text"] { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
                    input[type="submit"] { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
                    input[type="submit"]:hover { background-color: #0056b3; }
                    .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>KODI 视频嗅探远程输入</h2>
                    <p>请在下方粘贴视频网页地址：</p>
                    <form action="/submit" method="post">
                        <input type="text" name="url" placeholder="https://..." required><br>
                        <input type="submit" value="发送到 KODI">
                    </form>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            url = params.get('url', [None])[0]
            
            if url:
                global received_url
                received_url = url
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                response = """
                <html><body>
                <h2 style="text-align:center; color:green;">发送成功！</h2>
                <p style="text-align:center;">KODI 正在解析视频，请查看电视屏幕。</p>
                <script>setTimeout(function(){ window.location.href = '/'; }, 3000);</script>
                </body></html>
                """
                self.wfile.write(response.encode('utf-8'))
            else:
                self.send_error(400, "Invalid URL")
        else:
            self.send_error(404)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 不需要真正连接，只是为了获取本地 IP
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def start_server(port=8080):
    global server_instance
    handler = RemoteInputHandler
    server_instance = socketserver.ThreadingTCPServer(("", port), handler)
    print(f"Starting server at port {port}")
    server_thread = threading.Thread(target=server_instance.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return f"http://{get_local_ip()}:{port}"

def stop_server():
    global server_instance
    if server_instance:
        server_instance.shutdown()
        server_instance.server_close()
        server_instance = None

def get_received_url():
    global received_url
    url = received_url
    received_url = None # 获取后重置
    return url
