#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   发起http请求的相关方法和http信息
"""
import requests
import base64
import pickle
from collections import OrderedDict
from wsgiref.util import is_hop_by_hop

import config


'''
    httplib版本:https://github.com/whitmo/WSGIProxy/blob/master/wsgiproxy/exactproxy.py:proxy_exact_request
'''
def call_http_request(url, method, req_headers=None, req_data=None, req_query_string=None, **kwargs):
    if config.DEBUG:
        from requests.models import RequestEncodingMixin

        print 'call http %s%s' % (
        url, '?' + RequestEncodingMixin._encode_params(req_query_string) if req_query_string else '')
    return getattr(requests, method.lower())('%s' % url, params=req_query_string, data=req_data, headers=req_headers,
                                             **kwargs)


class HttpInfo(object):
    def __init__(self, method, url, req_query_string, req_headers, req_data, status_code, res_headers):
        # http method type | 请求类型，如GET
        self.method = method
        # http url | 请求URL地址，包含domain和port，没有加上query string
        self.url = url
        # query string | 在url '?'后面跟着的
        self.req_query_string = req_query_string
        # request headers | 请求头
        self.req_headers = self.sort_headers(req_headers)
        # request data | http请求 data
        self.req_data = req_data
        # http status code | http 状态码
        self.status_code = status_code
        # http respond headers | 返回头
        self.res_headers = self.sort_headers(res_headers)

    def dumps(self):
        # 序列化
        return base64.encodestring(pickle.dumps(dict(method=self.method, url=self.url,
                                                     req_query_string=self.req_query_string,
                                                     req_headers=self.req_headers, req_data=self.req_data,
                                                     status_code=self.status_code, res_headers=self.res_headers)))

    @staticmethod
    def loads(_str):
        # 反序列化
        return HttpInfo(**pickle.loads(base64.decodestring(_str)))

    @staticmethod
    def sort_headers(headers):
        # 根据headers name 进行排序
        assert hasattr(headers, "__iter__")
        return OrderedDict(sorted(headers.iteritems(), key=lambda d: d[0]))


def parse_requests_result(result):
    headers = result.headers
    for key, val in headers.iteritems():
        if is_hop_by_hop(key):
            headers.pop(key)
        elif key.lower() == 'content-encoding' and 'zip' in val:
            headers.pop(key)
    status_code = result.status_code
    output = result.content
    # 重新排序header，保持与缓存返回的一致性
    headers = HttpInfo.sort_headers(headers)
    return status_code, headers, output


def get_http_result(**kwargs):
    return parse_requests_result(call_http_request(**kwargs))