#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/18
Desc    :   
"""
import sys,os

os.environ.setdefault("APPENGINE_SETTINGS_MODULE", "requestspool.config")
project_loc = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(project_loc)

from unittest import TestCase as BaseTestCase
import requests
import datetime
import config
from requestspool.cache import cache, CACHE_RESULT, CACHE_RESULT_TYPE, CACHE_CONTROL, CACHE_CONTROL_TYPE


SERVICE_URI = 'http://localhost:%s/' % config.PORT


class Settings(object):
    def statistics_baidu_req_time(self):
        if "AvgBdReqTime" not in globals():
            retry_count = 3

            def get():
                d1 = datetime.datetime.now()
                r = requests.get(u'http://www.baidu.com')
                d2 = datetime.datetime.now()
                return d2-d1
            bd_time = 0
            for i in range(retry_count):
                bd_time += get().total_seconds()
            globals()["AvgBdReqTime"] = bd_time/retry_count
        return globals()["AvgBdReqTime"]

    def get_test_url1(self):
        # 请自行决定测试url
        import test_config
        return test_config.Test_url1

    def get_test_url2(self):
        # 请自行决定测试url
        import test_config
        return test_config.Test_url2


    AvgBdReqTime = property(statistics_baidu_req_time)
    TestUrl1 = property(get_test_url1)
    TestUrl2 = property(get_test_url2)

settings = Settings()


class TestCase(BaseTestCase):
    def count_time(self, func, args=tuple(), kwargs=None):
        if not kwargs:
            kwargs = {}
        d1 = datetime.datetime.now()
        result = func(*args, **kwargs)
        d2 = datetime.datetime.now()
        return d2 - d1, result


def get_max_cache_time():
    return settings.AvgBdReqTime if settings.AvgBdReqTime > 0.1 else 0.1


'''
    httplib版本:https://github.com/whitmo/WSGIProxy/blob/master/wsgiproxy/exactproxy.py:proxy_exact_request
'''
def call_http_request(url, method, req_headers=None, req_data=None, req_query_string=None, **kwargs):
    d1 = datetime.datetime.now()
    result = getattr(requests, method.lower())('%s' % url, params=req_query_string, data=req_data, headers=req_headers,
                                             **kwargs)
    d2 = datetime.datetime.now()
    from requests.models import RequestEncodingMixin

    print 'call http %s%s time:%s' % (url,
      '?' + RequestEncodingMixin._encode_params(req_query_string) if req_query_string else '',(d2-d1).total_seconds())
    return result


class TestReqInfo(object):
    def __init__(self, method, url, req_query_string=None, req_headers=None, req_data=None):
        self.method, self.url, self.req_query_string, self.req_headers, self.req_data = \
            method, url, req_query_string, req_headers, req_data

    def delete(self):
        return cache.delete(
            url=self.url, method=self.method, req_headers=self.req_headers,
            req_data=self.req_data, req_query_string=self.req_query_string
        )

    def get_id(self):
        return cache.get_id(
            url=self.url, method=self.method, req_headers=self.req_headers,
            req_data=self.req_data, req_query_string=self.req_query_string
        )

    def get_cache_http_info(self):
        return cache.find_httpinfo(self.get_id())

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
        result = call_http_request(**req_dict)
        if CACHE_RESULT not in result.headers:
            print "没有缓存控制,headers%s: result:%s" % (dict(result.headers), result.content[:20])
        # 检查缓存是否存在
        if not cache.find_httpinfo(cache.get_id(self.method, self.url, self.req_query_string,
                                   self.req_headers, self.req_data)):
            print "缓存没有保存成功"
        return result