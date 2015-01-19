#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/29
Desc    :   缓存更新控制器,具体实现需要继承interface.BaseUpdate
"""
from interface import BaseUpdate, BaseRoute
import datetime
import gevent.lock
from Queue import Queue, Full, Empty
import gevent

from requestspool.cache import cache
import config
from .util import get_route, backend_call


class BaseSetQueue(object):
    def __init__(self, maxsize=0):
        self._queue = Queue(maxsize)
        self.id_set = set()

    @staticmethod
    def _over_length_item(item):
        print u"太多后台连接了,清除最后一个请求:", item

    def __len__(self):
        return len(self.id_set)


class SetQueue(BaseSetQueue):
    def __put(self, item, block=False, timeout=None):
        self._queue.put(item, block, timeout)
        self.id_set.add(item)

    def put(self, item, block=False, timeout=None):
        if item not in self.id_set:
            try:
                self.__put(item, block, timeout)
            except Full:
                self._over_length_item(self.get())
                self.__put(item, block, timeout)

    def get(self, block=False, timeout=None):
        item = self._queue.get(block, timeout)
        self.id_set.remove(item)
        return item


class HttpSetQueue(BaseSetQueue):
    # 不阻塞,直接抛出异常

    def __put(self, item, _id=None):
        if not _id:
            _id = item
        self._queue.put(item)
        self.id_set.add(_id)

    def put(self, **kwargs):
        _id = cache.get_id(**kwargs)
        if _id not in self.id_set:
            try:
                self.__put(kwargs, _id=_id)
            except Full:
                self._over_length_item(self.get())
                self.__put(kwargs, _id=_id)

    def get(self):
        item = self._queue.get()
        _id = cache.get_id(**item)
        self.id_set.remove(_id)
        return item


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


class BackendRun(object):
    def __init__(self):
        self._queue = HttpSetQueue(config.BACKEND_RUNNER_COUNT)
        self._empty_lock = gevent.lock.BoundedSemaphore(1)
        # 开始之后为0,锁住
        self._empty_lock.acquire()

    def __enter__(self):
        if len(self._queue) == 0:
            self._empty_lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add(self, **kwargs):
        self._queue.put(**kwargs)
        try:
            self._empty_lock.release()
        except ValueError:
            pass

    def __call__(self):
        # 非阻塞,从内存中拿到请求的参数
        try:
            kwargs = self._queue.get()
        except Empty:
            return
        route = kwargs.pop("route")
        if not route or not isinstance(route, BaseRoute):
            return
        backend_call(route.call_http_request, **kwargs)

    def __len__(self):
        return len(self._queue)