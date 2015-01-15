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
from wsgiref.util import is_hop_by_hop

from . import config
from . import httpinfo
from .interface import BaseHttpInfo


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


def parse_requests_result(result):
    headers = result.headers
    for key, val in headers.iteritems():
        if is_hop_by_hop(key):
            headers.pop(key)
        elif key.lower() == 'content-encoding' and 'zip' in val:
            headers.pop(key)
    status_code = result.status_code
    output = result.content
    if 'Content-Length' in headers:
        # 让wsgi模块自行计算解压之后的字节大小
        headers.pop('Content-Length')
    return status_code, headers, output


def get_http_result(**kwargs):
    return parse_requests_result(call_http_request(**kwargs))


def get_HttpInfo_class(version):
    return getattr(httpinfo, "HttpInfoVersion%s" % version)

HttpInfo = get_HttpInfo_class(config.DEFAULT_HTTPINFO_VERSION)
assert issubclass(HttpInfo, BaseHttpInfo)
