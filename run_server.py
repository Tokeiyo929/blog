#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的 HTTP 服务器，用于运行本地网页
支持 Python 3.x
"""

import http.server
import socketserver
import os
import sys

# 设置端口号
PORT = 8000

# 切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 创建服务器
Handler = http.server.SimpleHTTPRequestHandler

class MyHTTPRequestHandler(Handler):
    def end_headers(self):
        # 添加 CORS 头，允许跨域请求
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

try:
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 60)
        print(f"服务器已启动！")
        print(f"访问地址: http://localhost:{PORT}")
        print(f"访问地址: http://127.0.0.1:{PORT}")
        print("=" * 60)
        print("按 Ctrl+C 停止服务器")
        print("=" * 60)
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n\n服务器已停止")
    sys.exit(0)
except OSError as e:
    if e.errno == 98 or e.errno == 48:  # Address already in use
        print(f"错误: 端口 {PORT} 已被占用")
        print(f"请尝试使用其他端口，或关闭占用该端口的程序")
    else:
        print(f"错误: {e}")
    sys.exit(1)

