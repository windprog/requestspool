#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   
"""
from abc import ABCMeta, abstractmethod

#
# 接口调用规范。
#


class BaseSpeed(object):
    __metaclass__ = ABCMeta

    def add_one(self):
        pass


class BaseCheckCallback(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, method, url, req_query_string, req_headers, req_data, status_code, res_headers, res_data):
        pass


class BaseUpdate(object):
    __metaclass__ = ABCMeta

    def __init__(self, expired, is_sync, save_check_callback=None, retry_limit=1, retry_check_callback=None):
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

        for callback in [save_check_callback, retry_check_callback]:
            if callback and not isinstance(callback, BaseCheckCallback):
                raise ValueError('%s must be BaseCheckCallback subclass instance' % callback.__name__)

    @abstractmethod
    def backend_call(self, method, url, req_query_string, req_headers, req_data):
        pass

    @abstractmethod
    def check_sync(self):
        pass

    @abstractmethod
    def get_expired_bool(self, method, url, req_query_string, req_headers, req_data, **kwargs):
        pass


class BaseRoute(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def match(self, url):
        pass


class BaseHttpCache(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def find(self, method, url, req_query_string, req_headers, req_data):
        pass

    @abstractmethod
    def get_update_time(self, method, url, req_query_string, req_headers, req_data):
        pass

    @abstractmethod
    def save(self, method, url, req_query_string, req_headers, req_data, status_code, res_headers, res_data):
        pass

    @abstractmethod
    def delete(self, method, url, req_query_string, req_headers, req_data):
        pass


