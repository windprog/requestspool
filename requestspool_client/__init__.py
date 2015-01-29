#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/29
Desc    :   
"""
import json
from StringIO import StringIO
import zlib
from collections import namedtuple


ConfigField = namedtuple("ConfigField", "MATCH FIELD COMPRESS")("match", "field", "compress")

CompressValues = namedtuple("CompressValues", "DEFAULT")("default")

# System field
METHOD, URL, REQ_QUERY_STRING, REQ_HEADERS, REQ_DATA, STATUS_CODE, RES_HEADERS, RES_DATA = \
    "method", "url", "req_query_string", "req_headers", "req_data", "status_code", "res_headers", "res_data"

# Control field
FILE_ID, AGAIN_LENGTH = "file_id", "again_length"

BASE64_FIELDS = {RES_DATA, REQ_DATA, URL, REQ_QUERY_STRING}

default_config = {
    ConfigField.MATCH: [
        # 监控所有下载
        ".*"
    ],
    ConfigField.FIELD: [
        # 以下为所有可用字段
        "method", "url", "req_query_string", "req_headers", "req_data", "status_code", "res_headers", "res_data"
    ],
    ConfigField.COMPRESS: CompressValues.DEFAULT,
}

'''
    连接广播服务
'''
def connect(service_url, config):
    try:
        # using  https://github.com/liris/websocket-client
        from websocket import create_connection
    except:
        raise ImportError("please install websocket-client.")
    ws = create_connection(service_url)
    ws.send(json.dumps(config))
    return ws


class Client(object):
    def __init__(self, host="localhost", port=8801, config=default_config):
        self._service_url = "ws://%s:%s/publish" % (host, port)
        self._config = {}
        if ConfigField.MATCH in config and isinstance(config.get(ConfigField.MATCH), list):
            self._config[ConfigField.MATCH] = config.get(ConfigField.MATCH)
        else:
            self._config[ConfigField.MATCH] = default_config.get(ConfigField.MATCH)
        if ConfigField.FIELD in config and isinstance(config.get(ConfigField.FIELD), list):
            self._config[ConfigField.FIELD] = config.get(ConfigField.FIELD)
        else:
            self._config[ConfigField.FIELD] = default_config.get(ConfigField.FIELD)
        if ConfigField.COMPRESS in config and isinstance(config[ConfigField.COMPRESS], basestring):
            self._config[ConfigField.COMPRESS] = config[ConfigField.COMPRESS]
        else:
            self._config[ConfigField.COMPRESS] = default_config.get(ConfigField.COMPRESS)
        self.compress_type = self._config[ConfigField.COMPRESS]
        self.ws = connect(self._service_url, self._config)

    def reconnect(self):
        try:
            # 断开旧连接
            self.ws.close()
        except:
            pass
        self.ws = connect(self._service_url, self._config)

    def receive(self):
        first = self.ws.recv()
        result = json.loads(first)
        assert isinstance(result, dict)
        if AGAIN_LENGTH in result:
            # 存在续传
            count = 0
            total = result[AGAIN_LENGTH]
            sio = StringIO()
            while count < total:
                tmp = self.ws.recv()
                sio.write(tmp)
                count += len(tmp)
            sio.seek(0)
            _str = sio.read()
            if self.compress_type == CompressValues.DEFAULT:
                _str = zlib.decompress(_str)
            result.update(json.loads(_str))
        for name in result.keys():
            if name in BASE64_FIELDS:
                result[name] = result[name].decode("base64")
        return result


def patch_requests(server="localhost:8801"):
    import requests
    import re
    server_url = "http://" + server
    try:
        # 获取路由
        routes = json.loads(requests.get(server_url + "/admin/route/all").content).get("route")
    except:
        print "尚未启动服务或服务运行异常"
        raise ImportError
    patterns = [re.compile(s) for s in routes if isinstance(s, basestring)]
    # patch
    old_request = requests.request

    def new_request(method, url, **kwargs):
        if url.startswith(server_url):
            return old_request(method, url, **kwargs)
        need_proxy = False
        for p in patterns:
            if p.match(url):
                need_proxy = True
                break
        if need_proxy:
            url = 'http://{server}/{url}'.format(server=server, url=url)
        return old_request(method, url, **kwargs)

    requests.request = new_request
