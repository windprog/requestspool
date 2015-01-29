#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/28
Desc    :   
"""
from gevent.event import AsyncResult
import re
import json
from StringIO import StringIO
from zip import zip_compress
from collections import namedtuple

from geventwebsocket.websocket import WebSocket


ConfigField = namedtuple("ConfigField", "MATCH FIELD COMPRESS")("match", "field", "compress")

CompressValues = namedtuple("CompressValues", "DEFAULT")("default")

# 系统字段
METHOD, URL, REQ_QUERY_STRING, REQ_HEADERS, REQ_DATA, STATUS_CODE, RES_HEADERS, RES_DATA = \
    "method", "url", "req_query_string", "req_headers", "req_data", "status_code", "res_headers", "res_data"

# 控制字段
FILE_ID, AGAIN_LENGTH = "file_id", "again_length"

ALL_FIELDS = {METHOD, URL, REQ_QUERY_STRING, REQ_HEADERS, REQ_DATA, STATUS_CODE, RES_HEADERS, RES_DATA, FILE_ID}

BASE64_FIELDS = {RES_DATA, REQ_DATA, URL, REQ_QUERY_STRING}

DICT_FIELDS = {REQ_HEADERS, RES_HEADERS}

BIG_DATA_FIELDS = {RES_DATA, REQ_DATA}

ONE_SEND_LENGTH = 1024


class ClientService(object):
    def __init__(self, _websocket, user_id, _config):
        self._user_id = user_id
        self._config = _config
        self._websocket = _websocket
        assert isinstance(self._websocket, WebSocket)

        matches = _config.get(ConfigField.MATCH)  # 订阅的条件， 目前是regex的字符串列表
        fields = _config.get(ConfigField.FIELD)  # 返回的订阅数据字段列表
        self.compress_type = CompressValues.DEFAULT \
            if ConfigField.COMPRESS in _config and _config[ConfigField.COMPRESS] else None

        self._patterns = []
        for item in matches:
            if isinstance(item, basestring):
                self._patterns.append(re.compile(item))
                if item not in self.all_patterns:
                    self.all_patterns[item] = {self._user_id}
                else:
                    self.all_patterns[item].add(self._user_id)

        self._fields = set([item for item in fields if item in ALL_FIELDS])

        # 存在file_id表明数据被持久化储存
        self._fields.add(FILE_ID)

        self._publish = AsyncResult()

        self.clients[user_id] = self

    def get_publish(self):
        result = self._publish.wait()
        self._publish = AsyncResult()
        return result

    fields = property(lambda o: o._fields)
    publish = property(get_publish, lambda o, v: o._publish.set(v))

    clients = {}
    all_patterns = {}

    def close(self):
        for k, v in self.all_patterns.items():
            assert isinstance(v, set)
            if self._user_id in v:
                v.remove(self._user_id)
            if len(v) == 0:
                self.all_patterns.pop(k)
        self.clients.pop(self._user_id, None)

    def get(self):
        # block
        return self._publish.get()

    def match(self, url):
        for p in self._patterns:
            if p.match(url):
                return True
        return False

    @classmethod
    def add(cls, **kwargs):
        # 找到所有需要广播的用户
        url = kwargs.get("url")
        all_user_id_set = set()
        for pattern_str, user_id_set in cls.all_patterns.iteritems():
            assert isinstance(user_id_set, set)
            # 使用系统自带的正则缓存
            p_obj = re.compile(pattern_str)
            if p_obj.match(url):
                all_user_id_set.update(user_id_set)

        # 数据格式化
        if FILE_ID in kwargs:
            kwargs[FILE_ID] = str(kwargs[FILE_ID])
        for name in kwargs.keys():
            if name in BASE64_FIELDS:
                # 编码成base64 方便转换成json
                kwargs[name] = kwargs[name].encode("base64")
            elif name in DICT_FIELDS:
                # 将请求头和返回头转换成dict
                kwargs[name] = dict(kwargs[name])
        # 广播
        for user_id in all_user_id_set:
            obj = cls.clients[user_id]
            obj.publish = {k: v for k, v in kwargs.iteritems() if k in obj.fields}

    def one_send(self):
        # 阻塞
        result = self.publish

        again_send = {}
        for k, v in result.items():
            if k in BIG_DATA_FIELDS:
                again_send[k] = result.pop(k)

        again_data = ""

        if len(again_send) > 0:
            again_data = json.dumps(again_send)
            if self.compress_type == CompressValues.DEFAULT:
                again_data = zip_compress(again_data)
            result[AGAIN_LENGTH] = len(again_data)

        self._websocket.send(json.dumps(result))
        if len(again_send) > 0:
            sio = StringIO(again_data)
            send_time = len(again_data) / (ONE_SEND_LENGTH * 1.0)
            for _ in xrange(int(send_time) + 1 if send_time > int(send_time) else int(send_time)):
                self._websocket.send(sio.read(ONE_SEND_LENGTH), True)



if __name__ == '__main__':
    c = ClientService(None, "0859113cd1d6486d84f8536f72ba4762", {u'match': [u'.*baidu.com'], u'field': [u'method', u'url', u'req_query_string', u'req_headers', u'req_data', u'status_code', u'res_headers', u'res_data']})
