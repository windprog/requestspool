#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   接口调用规范。
"""
from requests.structures import CaseInsensitiveDict
from abc import ABCMeta, abstractmethod


class BaseSpeed(object):
    __metaclass__ = ABCMeta

    def add_one(self):
        pass


class BaseCheckCallback(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, method, url, req_query_string, req_headers, req_data, status_code, res_headers, res_data):
        # 根据http请求结果判断
        pass

    @staticmethod
    def sleep(seconds=0):
        import gevent
        gevent.sleep(seconds)


class BaseUpdate(object):
    __metaclass__ = ABCMeta

    def __init__(self, expired=0, is_sync=True, save_check_callback=None, retry_limit=1, retry_check_callback=None,
                 requests_timeout=None):
        # 缓存过期时间，单位秒
        self.expired = expired
        # 过期时获取的动作，True为等待最新数据完成才返回
        self.is_sync = is_sync
        # 检测是否需要储存缓存
        self.save_check_callback = save_check_callback
        # 检测是否需要重新尝试下载
        self.retry_check_callback = retry_check_callback
        # 重试次数，默认为1
        self.retry_limit = 1
        # 请求超时
        self.requests_timeout = requests_timeout

        for callback in [save_check_callback, retry_check_callback]:
            if callback and not isinstance(callback, BaseCheckCallback):
                raise ValueError('%s must be BaseCheckCallback subclass instance' % callback.__name__)

    @abstractmethod
    def check_sync(self):
        # 检测是否阻塞执行
        pass

    @abstractmethod
    def is_expired_incache(self, method, url, req_query_string, req_headers, req_data, **kwargs):
        # 返回元组()  第一个为是否过期,第二个为是否在缓存中
        pass


class BaseRoute(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def match(self, url):
        # 检测url是否满足本路由条件
        pass


class BaseHttpCache(object):
    __metaclass__ = ABCMeta
    # id字符串长度
    ID_LENGTH = 56

    @staticmethod
    def get_id(method, url, req_query_string, req_headers, req_data, **kwargs):
        pass

    @abstractmethod
    def find(self, method, url, req_query_string, req_headers, req_data):
        # 返回HttpInfo对象和res_data
        pass

    @abstractmethod
    def find_httpinfo(self, _id):
        # 用缓存id返回返回HttpInfo对象
        pass

    @abstractmethod
    def get_update_time(self, method, url, req_query_string, req_headers, req_data):
        # 获取缓存上一次更新时间
        pass

    @abstractmethod
    def save(self, method, url, req_query_string, req_headers, req_data, status_code, res_headers, res_data):
        # 保存缓存
        pass

    @abstractmethod
    def delete(self, method, url, req_query_string, req_headers, req_data):
        # 删除缓存
        pass


class BaseHttpInfo(object):
    __metaclass__ = ABCMeta
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

    @staticmethod
    def get_id(method, url, req_query_string, req_headers, req_data):
        pass

    @staticmethod
    def loads(_str):
        pass

    @abstractmethod
    def dumps(self):
        pass
