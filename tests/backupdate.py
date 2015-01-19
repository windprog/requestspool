#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/19
Desc    :   
"""
import datetime
import time

from base import TestReqInfo, TestCase, get_route, CACHE_RESULT, CACHE_RESULT_TYPE, settings, get_max_cache_time
import gevent.monkey
import gevent
gevent.monkey.patch_all()


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
        self.check_cache_result(s2, r2)  # 取缓存时间小于 下载时间
        # 测试is_sync
        # reset clock
        # 强制缓存过期
        route = get_route(self.req.url)
        if route._update.is_sync:
            expired = route._update.expired
            time.sleep(expired)

            s3, r3 = self.count_time(self.req.req)
            self.assertTrue(r3.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.NEW)
            # 需要下载
            self.assertTrue(s3 > s2)  # 下载时间大于取缓存时间
            self.assertTrue(s3.total_seconds() < 3)  # 下载时间小于3秒
            self.assertTrue(s3.total_seconds() > settings.AvgBdReqTime/4)  # 下载时间 大于 平均下载时间的四分之一
        else:
            expired = route._update.expired
            time.sleep(expired)

            jobs = []
            jobs.append(gevent.spawn(self.count_time, self.req.req))
            time.sleep(0.001)
            # 删除旧缓存
            jobs.append(gevent.spawn(self.req.delete))
            time.sleep(0.001)
            gevent.joinall(jobs)
            s3, r3 = jobs[0].value
            self.assertTrue(self.req.is_incache())
            # 取缓存
            self.assertTrue(r3.headers.get(CACHE_RESULT) == CACHE_RESULT_TYPE.OLD)
            self.assertTrue(s3 < s1)
            self.check_cache_result(s3, r3)  # 取缓存时间小于 下载时间