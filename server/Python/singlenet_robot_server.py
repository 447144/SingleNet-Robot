#!/usr/bin/env python3
# coding=utf-8

"""
SingleNet Robot Python3 Server
Version: 3.0
Author: Eugene Wu <kuretru@gmail.com>
URL: https://github.com/kuretru/SingleNet-Robot
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import subprocess
import time

PORT = 8079  # 闪讯机器人API服务器监听端口
ACCESS_TOKEN = '123456'  # RESTful API通信密钥


def ping():
    now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    return success_response(now)


def get_network_option(network_interface: str):
    username = run_subprocess(['uci', 'get', 'network.{}.username'.format(network_interface)])
    password = run_subprocess(['uci', 'get', 'network.{}.password'.format(network_interface)])
    return success_response({'username': username, 'password': password})


def set_network_option(network_interface: str, username: str, password: str):
    if username is not None and len(username) > 0:
        run_subprocess(['uci', 'set', 'network.{}.username={}'.format(network_interface, username)])
    if password is not None and len(password) > 0:
        run_subprocess(['uci', 'set', 'network.{}.password={}'.format(network_interface, password)])
    run_subprocess(['uci', 'commit', 'network.{}'.format(network_interface)])
    return get_network_option(network_interface)


def get_interface_status(network_interface: str):
    result = run_subprocess(['/sbin/ifstatus', network_interface])
    return success_response(json.loads(result))


def set_interface_up(network_interface: str):
    run_subprocess(['/sbin/ifdown', network_interface, '&&', '/sbin/ifup', network_interface])
    return get_interface_status(network_interface)


def success_response(data):
    return build_response(100, 'success', data)


def build_response(code: int, message: str, data, status_code=200):
    body = {'code': code, 'message': message, 'data': data}
    return {'body': body, 'status_code': status_code}


def run_subprocess(args):
    output = subprocess.run(args, capture_output=True, check=True)
    return output.stdout.decode().replace('\n', '').strip()


class SingleNetRequestHandler(BaseHTTPRequestHandler):
    routes = []

    def ping(self):
        return ping()

    def get_network_option(self):
        params = parse_qs(urlparse(self.path).query)
        return get_network_option(params['interface'][0])

    def set_network_option(self):
        data = self._get_request_body()
        return set_network_option(data['interface'], data['username'], data['password'])

    def get_interface_status(self):
        params = parse_qs(urlparse(self.path).query)
        return get_interface_status(params['interface'][0])

    def set_interface_up(self):
        data = self._get_request_body()
        return set_interface_up(data['interface'])

    def _prepare_request(self, method: str):
        """预处理HTTP Request"""
        if 'Access-Token' not in self.headers:
            self._prepare_response(build_response(10200, 'user authentication failed', '请求头未携带Access-Token', 401))
            return
        access_token = self.headers['Access-Token']
        if not self._valid_access_token(access_token):
            self._prepare_response(build_response(10200, 'user authentication failed', 'Access-Token错误', 401))
            return
        for route in SingleNetRequestHandler.routes:
            path = urlparse(self.path).path
            if path == route['path'] and method == route['method']:
                try:
                    self._handle_request(route['handler'])
                except subprocess.CalledProcessError as e:
                    output = e.stderr.decode().replace('\n', '').strip()
                    self._prepare_response(build_response(10400, 'user request error', '命令执行出错：' + output, 500))
                except Exception as e:
                    output = e.strerror
                    self._prepare_response(build_response(10400, 'user request error', '命令执行出错：' + output, 500))
                return
        self._prepare_response(build_response(10400, 'user request error', '不存在该路由', 404))

    def _handle_request(self, handler):
        self._prepare_response(handler(self))

    def _get_request_body(self):
        content_length = int(self.headers.get('Content-Length'))
        request_body = self.rfile.read(content_length).decode()
        return json.loads(request_body)

    def _prepare_response(self, data: dict):
        """封装HTTP Response Body"""
        self.send_response(data['status_code'])
        self._send_response(data['body'])

    def _send_response(self, body):
        """封装HTTP Response"""
        body = json.dumps(body, ensure_ascii=False)
        data = body.encode('UTF-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(data)

    def _valid_access_token(self, access_token: str):
        """验证Access-Token的合法性，暂时直接比对"""
        return ACCESS_TOKEN == access_token

    def do_method(self, method: str):
        self._prepare_request(method)

    def do_OPTIONS(self):
        self.do_method('OPTIONS')

    def do_GET(self):
        self.do_method('GET')

    def do_HEAD(self):
        self.do_method('HEAD')

    def do_POST(self):
        self.do_method('POST')

    def do_PUT(self):
        self.do_method('PUT')

    def do_DELETE(self):
        self.do_method('DELETE')

    def do_TRACE(self):
        self.do_method('TRACE')

    def do_CONNECT(self):
        self.do_method('CONNECT')


if __name__ == '__main__':
    SingleNetRequestHandler.routes = [
        {'path': '/api/ping', 'method': 'GET', 'handler': SingleNetRequestHandler.ping},
        {'path': '/api/network/option', 'method': 'GET', 'handler': SingleNetRequestHandler.get_network_option},
        {'path': '/api/network/option', 'method': 'POST', 'handler': SingleNetRequestHandler.set_network_option},
        {'path': '/api/network/status', 'method': 'GET', 'handler': SingleNetRequestHandler.get_interface_status},
        {'path': '/api/network/status', 'method': 'POST', 'handler': SingleNetRequestHandler.set_interface_up}
    ]
    httpd = HTTPServer(('0.0.0.0', PORT), SingleNetRequestHandler)
    print('Starting SingleNet Robot RESTful API Server at port %d' % PORT)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print('Stopping SingleNet Robot RESTful API Server')
    httpd.server_close()
