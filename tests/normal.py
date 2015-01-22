#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/5
Desc    :   
"""
from base import TestCase, TestReqInfo, SERVICE_URI, call_http_request, get_route, settings, \
    cache, CACHE_RESULT, CACHE_RESULT_TYPE, CACHE_CONTROL, CACHE_CONTROL_TYPE, \
    get_max_cache_time
import requests
import datetime
import time

from requestspool import config


def check():
    # 检测服务运行是否正常
    return 'Running' in requests.get(SERVICE_URI + 'check').text


print 'statistics baidu request time: %s' % settings.AvgBdReqTime


class CacheClassTestCase(TestCase):
    def test_get_id(self):
        id1 = cache.get_id(u'GET', u'http://www.baidu.com', u'c=1&b=3&d=1&a=9', {}, '')
        id2 = cache.get_id(u'GET', u'http://www.baidu.com', u'a=9&c=1&b=3&d=1', {}, '')
        if config.RESORT_QUERY_STRING:
            self.assertTrue(id1 == id2)
        else:
            self.assertTrue(id1 != id2)


class CacheHttpTestCase(TestCase):
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

    def check_cache_result(self, req_time, res):
        self.assertTrue(res.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.OLD)
        self.assertTrue(req_time.total_seconds() < get_max_cache_time())  # 取缓存时间小于 下载时间

    def test_incache(self):
        s1, r1 = self.count_time(self.req.req)
        s2, r2 = self.count_time(self.req.req)
        s3, r3 = self.count_time(self.req.req)
        s4, r4 = self.count_time(self.req.req)
        print 'project get cache avg time: %s' % ((s2+s3+s4).total_seconds()/3)
        self.assertTrue(r1.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.NEW)
        self.assertTrue(s2 < s1)
        self.check_cache_result(s3, r3)
        self.check_cache_result(s4, r4)

    def test_nocachre(self):
        s, r = self.count_time(self.req.req)
        self.assertTrue(r.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.NEW)
        # 下载时间 大于 平均下载时间的四分之一
        self.assertTrue(s.total_seconds() > settings.AvgBdReqTime/4)

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
        print 'waittime: %s' % (s2.total_seconds() + s1.total_seconds())
        self.assertTrue(s2.total_seconds() + s1.total_seconds() > count_time / 1000.0)
        # 访问百度的时间不超过3秒
        self.assertTrue(s2.total_seconds() + s1.total_seconds() < (count_time / 1000.0) + 3)
