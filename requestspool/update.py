#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/29
Desc    :   缓存更新控制器,具体实现需要继承interface.BaseUpdate
"""
from interface import BaseUpdate
import datetime
import gevent

from requestspool.cache import cache
import config


class Update(BaseUpdate):
    def check_sync(self):
        return self.is_sync

    def is_expired_incache(self, **kwargs):
        # True为缓存过期
        update_time = self.get_update_time(**kwargs)
        is_expired = update_time and (datetime.datetime.now() - update_time).total_seconds() > self.expired
        is_in_cache = True if update_time else False
        return is_expired, is_in_cache

    @staticmethod
    def get_update_time(method, url, req_query_string, req_headers, req_data):
        return cache.get_update_time(method=method, url=url, req_query_string=req_query_string,
                                     req_headers=req_headers, req_data=req_data)

    def backend_call(self, _route, **kwargs):
        gevent.spawn(_route.call_http_request, **kwargs)


class DebugUpdate(Update):
    def backend_call(self, _route, **kwargs):
        import threading

        t = threading.Thread(target=_route.call_http_request, kwargs=kwargs)
        t.start()


if config.DEBUG:
    Update = DebugUpdate
