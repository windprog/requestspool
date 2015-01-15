#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/15
Desc    :   缓存id计算和httpinfo对象,引用类请在http.py内饮用HttpInfo
            请保证完善的测试
"""
import hashlib
import base64
import pickle
from collections import OrderedDict
from requests.structures import CaseInsensitiveDict

from .interface import BaseHttpInfo
from . import config


class HttpInfoVersion1(BaseHttpInfo):
    def __init__(self, method, url, req_query_string, req_headers, req_data, status_code, res_headers):
        # http method type | 请求类型，如GET
        self.method = method
        # http url | 请求URL地址，包含domain和port，没有加上query string
        self.url = url
        # query string | 在url '?'后面跟着的
        self.req_query_string = req_query_string
        # request headers | 请求头
        self.req_headers = req_headers
        # request data | http请求 data
        self.req_data = req_data
        # http status code | http 状态码
        self.status_code = status_code
        # http respond headers | 返回头
        self.res_headers = res_headers if isinstance(res_headers, CaseInsensitiveDict) \
            else CaseInsensitiveDict(res_headers)

    def dumps(self):
        # 序列化
        return base64.encodestring(pickle.dumps(dict(method=self.method, url=self.url,
                                                     req_query_string=self.req_query_string,
                                                     req_headers=self.req_headers, req_data=self.req_data,
                                                     status_code=self.status_code, res_headers=self.res_headers)))

    @staticmethod
    def loads(_str):
        # 反序列化
        return HttpInfoVersion1(**pickle.loads(base64.decodestring(_str)))

    @staticmethod
    def sort_headers(headers):
        # 根据headers name 进行排序
        assert hasattr(headers, "__iter__")
        return OrderedDict(sorted(headers.iteritems(), key=lambda d: d[0]))

    @staticmethod
    def get_id(method, url, req_query_string, req_headers, req_data):
        # 根据请求头hash 取样  req_headers是None or 字典
        if config.RESORT_QUERY_STRING:
            # 参数重新排序,让参数排序不一致的 url 获取一样的id
            rqs_split = req_query_string.split(u'&')
            rqs_split.sort()
            req_query_string = u'&'.join(rqs_split)
        r_list = [method, url, req_query_string,
                  # request headers 暂不参与缓存id计算 | 注释内容为：排序之后将dict key value 直接连接起来
                  # "".join([key + str(val) for key, val in
                  #          HttpInfoVersion1.sort_headers(req_headers).iteritems()]) if req_headers else '',
                  req_data if req_data else '']
        return hashlib.sha224(u"".join(r_list)).hexdigest()
