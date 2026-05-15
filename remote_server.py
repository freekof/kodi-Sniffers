import http.server
import socketserver
import threading
import socket
import urllib.parse
import html

# 全局变量用于存储接收到的操作
received_action = None
server_instance = None
history_provider = None


def set_history_provider(provider):
    global history_provider
    history_provider = provider


def get_history_records():
    if history_provider:
        try:
            return history_provider()
        except Exception:
            return []
    return []


def build_home_page(records):
    history_items = []
    for index, record in enumerate(records):
        title = html.escape(record.get('title') or '未知标题')
        thumbnail = html.escape(record.get('thumbnail') or '')
        image = f'<img src="{thumbnail}" alt="" class="thumb">' if thumbnail else '<div class="thumb placeholder">无图</div>'
        history_items.append(f'''
                    <a class="history-card" href="/history/{index}">
                        {image}
                        <div class="history-title">{title}</div>
                    </a>''')

    history_html = '\n'.join(history_items) if history_items else '<p class="empty">暂无嗅探记录</p>'
    return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>KODI Video Sniffer Remote Input</title>
                <style>
                    body {{ font-family: sans-serif; padding: 16px; background-color: #f0f0f0; color: #222; }}
                    h2, h3 {{ margin: 8px 0 12px; }}
                    form {{ margin: 0 0 18px; }}
                    input[type="text"] {{ box-sizing: border-box; width: 100%; padding: 11px; margin: 8px 0; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }}
                    input[type="submit"], button {{ width: 100%; background-color: #007bff; color: white; padding: 11px 18px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }}
                    .play-button {{ background-color: #28a745; }}
                    .container {{ max-width: 760px; margin: 0 auto; background-color: white; padding: 18px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .section {{ border-top: 1px solid #eee; padding-top: 16px; margin-top: 16px; }}
                    .hint {{ color: #666; font-size: 14px; line-height: 1.5; }}
                    .history-list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }}
                    .history-card {{ display: block; overflow: hidden; color: inherit; text-decoration: none; border: 1px solid #ddd; border-radius: 8px; background: #fafafa; }}
                    .thumb {{ width: 100%; aspect-ratio: 16 / 9; object-fit: cover; display: block; background: #ddd; }}
                    .placeholder {{ display: flex; align-items: center; justify-content: center; color: #777; }}
                    .history-title {{ padding: 8px; font-size: 14px; line-height: 1.35; }}
                    .empty {{ color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>KODI 视频嗅探远程输入</h2>
                    <p class="hint">输入视频网页地址会交给 yt-dlp 嗅探；输入 m3u8、mp4 等直链可直接发送到 KODI 播放。</p>

                    <form action="/submit" method="post">
                        <h3>嗅探网页视频</h3>
                        <input type="text" name="url" placeholder="https://example.com/video-page" required>
                        <input type="submit" value="嗅探并发送到 KODI">
                    </form>

                    <div class="section">
                        <form action="/play" method="post">
                            <h3>直接播放链接</h3>
                            <input type="text" name="play_url" placeholder="https://example.com/live.m3u8 或 video.mp4" required>
                            <input class="play-button" type="submit" value="直接播放">
                        </form>
                    </div>

                    <div class="section">
                        <h3>嗅探记录</h3>
                        <div class="history-list">
                            {history_html}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''


def build_history_detail_page(record):
    title = html.escape(record.get('title') or '未知标题')
    thumbnail = html.escape(record.get('thumbnail') or '')
    image = f'<img src="{thumbnail}" alt="" class="hero">' if thumbnail else ''
    stream_items = []
    for stream in record.get('streams', []):
        label = html.escape(stream.get('label') or '未知格式')
        url = html.escape(stream.get('url') or '')
        stream_items.append(f'''
                    <div class="stream">
                        <div class="stream-label">{label}</div>
                        <input class="stream-url" type="text" value="{url}" readonly onclick="this.select()">
                        <button type="button" onclick="copyStreamUrl(this)">复制地址</button>
                        <form action="/play" method="post">
                            <input type="hidden" name="play_url" value="{url}">
                            <input type="submit" value="播放此地址">
                        </form>
                    </div>''')
    streams_html = '\n'.join(stream_items) if stream_items else '<p class="empty">此记录没有可播放流。</p>'

    return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>{title}</title>
                <style>
                    body {{ font-family: sans-serif; padding: 16px; background-color: #f0f0f0; color: #222; }}
                    .container {{ max-width: 760px; margin: 0 auto; background-color: white; padding: 18px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .hero {{ width: 100%; border-radius: 8px; margin: 8px 0 14px; }}
                    .stream {{ border-top: 1px solid #eee; padding: 14px 0; }}
                    .stream-label {{ font-weight: bold; margin-bottom: 8px; }}
                    .stream-url {{ box-sizing: border-box; width: 100%; color: #555; font-size: 13px; margin-bottom: 8px; padding: 9px; border: 1px solid #ccc; border-radius: 6px; }}
                    input[type="submit"], button {{ width: 100%; color: white; padding: 10px 18px; border: none; border-radius: 6px; font-size: 16px; margin-bottom: 8px; }}
                    button {{ background-color: #007bff; }}
                    input[type="submit"] {{ background-color: #28a745; }}
                    a {{ color: #007bff; text-decoration: none; }}
                    .empty {{ color: #777; }}
                </style>
                <script>
                    function copyStreamUrl(button) {{
                        var input = button.parentElement.querySelector('.stream-url');
                        input.select();
                        input.setSelectionRange(0, 999999);
                        if (navigator.clipboard && navigator.clipboard.writeText) {{
                            navigator.clipboard.writeText(input.value);
                        }} else {{
                            document.execCommand('copy');
                        }}
                        button.textContent = '已复制';
                        setTimeout(function() {{ button.textContent = '复制地址'; }}, 1500);
                    }}
                </script>
            </head>
            <body>
                <div class="container">
                    <p><a href="/">返回首页</a></p>
                    <h2>{title}</h2>
                    {image}
                    <h3>嗅探结果</h3>
                    {streams_html}
                </div>
            </body>
            </html>
            '''


def set_received_sniff_url(url):
    global received_action
    received_action = {'type': 'sniff', 'url': url}


def set_received_direct_play_url(url):
    global received_action
    received_action = {'type': 'play', 'url': url}

class RemoteInputHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(build_home_page(get_history_records()).encode('utf-8'))
        elif self.path.startswith('/history/'):
            try:
                index = int(self.path.rsplit('/', 1)[1])
                record = get_history_records()[index]
            except Exception:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(build_history_detail_page(record).encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            url = params.get('url', [None])[0]
            
            if url:
                set_received_sniff_url(url)
                self._send_success_page('发送成功！', 'KODI 正在嗅探视频，请查看电视屏幕。')
            else:
                self.send_error(400, "Invalid URL")
        elif self.path == '/play':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            url = params.get('play_url', [None])[0]

            if url:
                set_received_direct_play_url(url)
                self._send_success_page('发送成功！', 'KODI 正在直接播放此地址，请查看电视屏幕。')
            else:
                self.send_error(400, "Invalid URL")
        else:
            self.send_error(404)

    def _send_success_page(self, title, message):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        response = f"""
        <html><body>
        <h2 style="text-align:center; color:green;">{html.escape(title)}</h2>
        <p style="text-align:center;">{html.escape(message)}</p>
        <script>setTimeout(function(){{ window.location.href = '/'; }}, 3000);</script>
        </body></html>
        """
        self.wfile.write(response.encode('utf-8'))

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

def start_server(port=8080, history_provider_func=None):
    global server_instance
    set_history_provider(history_provider_func)
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

def get_received_action():
    global received_action
    action = received_action
    received_action = None # 获取后重置
    return action


def get_received_url():
    action = get_received_action()
    if action and action.get('type') == 'sniff':
        return action.get('url')
    return None
