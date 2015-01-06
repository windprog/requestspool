#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/5
Desc    :   
"""
from unittest import TestCase
import requests
import datetime
import time

import config
from requestspool.cache import cache, CACHE_RESULT, CACHE_RESULT_TYPE, CACHE_CONTROL, CACHE_CONTROL_TYPE
from requestspool.http import call_http_request
from requestspool.util import get_route

SERVICE_URI = 'http://localhost:%s/' % config.PORT


def check():
    # 检测服务运行是否正常
    return 'Running' in requests.get(SERVICE_URI + 'check').text


class TestReqInfo(object):
    def __init__(self, method, url, req_query_string=None, req_headers=None, req_data=None):
        self.method, self.url, self.req_query_string, self.req_headers, self.req_data = \
            method, url, req_query_string, req_headers, req_data

    def delete(self):
        return cache.delete(self.method, self.url, self.req_query_string, self.req_headers, self.req_data)

    def is_incache(self):
        update_time = cache.get_update_time(self.method, self.url, self.req_query_string,
                                            self.req_headers, self.req_data)
        return bool(update_time)

    def req(self, **kwargs):
        # url, method, req_headers, req_data, req_query_string
        req_dict = dict(
            url=SERVICE_URI + self.url, method=self.method, req_headers=self.req_headers,
            req_data=self.req_data, req_query_string=self.req_query_string
        )
        if kwargs:
            req_dict.update(kwargs)
        return call_http_request(**req_dict)


class CacheTestCase(TestCase):
    def setUp(self):
        # 新的请求
        self.req = TestReqInfo(
            method="GET", url="http://www.baidu.com", req_query_string='', req_headers={}, req_data=''
        )
        # 清理错误数据
        self.req.delete()
        self.start_time = datetime.datetime.now()

    def tearDown(self):
        print 'test total running time: %s' % (datetime.datetime.now()-self.start_time).total_seconds()
        # reset clock
        route = get_route(self.req.url)
        count_time = route._speed.count_time
        time.sleep(count_time/1000.0)
        self.req.delete()

    def count_time(self, func, args=tuple(), kwargs=None):
        if not kwargs:
            kwargs = {}
        d1 = datetime.datetime.now()
        result = func(*args, **kwargs)
        d2 = datetime.datetime.now()
        return d2 - d1, result

    def check_cache_result(self, req_time, res):
        self.assertTrue(res.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.OLD)
        self.assertTrue(req_time.total_seconds() < 0.1)  # 取缓存时间小于0.1秒

    def test_incache(self):
        s1, r1 = self.count_time(self.req.req)
        s2, r2 = self.count_time(self.req.req)
        s3, r3 = self.count_time(self.req.req)
        s4, r4 = self.count_time(self.req.req)
        self.assertTrue(r1.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.NEW)
        self.assertTrue(s2 < s1)
        self.check_cache_result(s3, r3)
        self.check_cache_result(s4, r4)
        print 'get avg cache time: %s' % ((s2+s3+s4).total_seconds()/3)

    def test_nocachre(self):
        s, r = self.count_time(self.req.req)
        self.assertTrue(r.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.NEW)
        self.assertTrue(s.total_seconds() > 0.1)

    def test_waittime(self):
        route = get_route(self.req.url)
        count_time, limit_req = route._speed.count_time, route._speed.limit_req
        # 强制检测limit为1
        self.assertTrue(limit_req == 1)
        s1, r1 = self.count_time(self.req.req)
        # 强制获取新数据
        s2, r2 = self.count_time(self.req.req, kwargs={
            'req_headers': {
                CACHE_CONTROL: CACHE_CONTROL_TYPE.SYNC
            }})
        self.assertTrue(s2.total_seconds() + s1.total_seconds() > count_time / 1000.0)
        # 访问百度的时间不超过3秒
        self.assertTrue(s2.total_seconds() + s1.total_seconds() < (count_time / 1000.0) + 3)

    '''
        过程为: 新的下载--取缓存--新的下载(or后台下载取缓存)
    '''
    def test_outinoutcache(self):
        # 需要下载
        s1, r1 = self.count_time(self.req.req)
        # 不需要下载
        s2, r2 = self.count_time(self.req.req)
        self.assertTrue(r1.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.NEW)
        self.assertTrue(r2.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.OLD)
        self.assertTrue(s1 > s2)  # 下载时间大于取缓存时间
        self.assertTrue(s2.total_seconds() < 0.1)  # 取缓存时间小于0.1秒
        # 测试is_sync
        # reset clock
        # 强制缓存过期
        route = get_route(self.req.url)
        expired = route._update.expired
        time.sleep(expired)

        s3, r3 = self.count_time(self.req.req)
        if route._update.is_sync:
            self.assertTrue(r3.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.NEW)
            # 需要下载
            self.assertTrue(s3 > s2)  # 下载时间大于取缓存时间
            self.assertTrue(s3.total_seconds() < 3)  # 下载时间小于3秒
            self.assertTrue(s3.total_seconds() > 0.1)  # 下载时间大于0.1秒
        else:
            # 取缓存
            self.assertTrue(r3.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.OLD)
            self.assertTrue(s3 < s1)
            self.assertTrue(s3.total_seconds() < 0.1)  # 取缓存时间小于0.1秒