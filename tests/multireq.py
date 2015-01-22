#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/18
Desc    :   
"""
from base import TestReqInfo
import gevent
import datetime

from gevent.monkey import patch_all
patch_all()

from base import settings


def same_req():
    try_time = 500
    req = TestReqInfo("GET", settings.TestUrl1,
        req_query_string="",
        req_headers={}, req_data="")
    # req.delete()
    jobs = []
    result = []

    from requests.exceptions import ConnectionError

    def save_callback(callback):
        try:
            r = callback()
        except ConnectionError:
            r = None
        result.append(r)

    for i in xrange(try_time):
        # 发起连接
        jobs.append(gevent.spawn(save_callback, req.req))

    d1 = datetime.datetime.now()
    gevent.joinall(jobs)
    d2 = datetime.datetime.now()

    server_error_count = 0
    speed_too_faster = 0
    connect_error_count = 0
    req_connect_error_count = 0
    other_count = 0
    timeout_count = 0
    normal_count = 0
    for i in xrange(try_time):
        if result[i] is None:
            connect_error_count += 1
        elif result[i].status_code not in [200, 400, 403, 404]:
            if result[i].status_code == 429:
                speed_too_faster += 1
            elif result[i].status_code == 500:
                server_error_count += 1
            elif result[i].status_code == 504:
                timeout_count += 1
            elif result[i].status_code == 503:
                req_connect_error_count += 1
            else:
                other_count += 1
        else:
            normal_count += 1


    print "并发%s 不同连接总共花的时间是: %s, 每秒: %s个连接" % (try_time, (d2-d1).total_seconds(), normal_count/(d2-d1).total_seconds())
    print "正常的连接数:%s" % normal_count
    print "统计过快的连接数:%s" % speed_too_faster
    print "服务器出错的连接数:%s" % server_error_count
    print "服务相应成功,但请求连接失败的连接数:%s" % req_connect_error_count
    print "超时的的连接数:%s" % timeout_count
    print "服务连接失败的连接数:%s" % connect_error_count
    print "其他错误的连接数:%s" % other_count


def no_same_req():
    try_time = 200
    for i in xrange(try_time):
        # 删除缓存
        req = TestReqInfo("GET", settings.TestUrl2 % i,
            req_query_string="",
            req_headers={}, req_data="")
        req.delete()


    jobs = []
    result = []
    from requests.exceptions import ConnectionError
    def save_callback(callback):
        try:
            r = callback()
        except ConnectionError:
            r = None
        result.append(r)

    for i in xrange(try_time):
        # 发起连接
        req = TestReqInfo("GET", settings.TestUrl2 % i,
            req_query_string="",
            req_headers={}, req_data="")
        jobs.append(gevent.spawn(save_callback, req.req))

    d1 = datetime.datetime.now()
    gevent.joinall(jobs)
    d2 = datetime.datetime.now()

    server_error_count = 0
    speed_too_faster = 0
    connect_error_count = 0
    req_connect_error_count = 0
    other_count = 0
    timeout_count = 0
    normal_count = 0
    for i in xrange(try_time):
        if result[i] is None:
            connect_error_count += 1
        elif result[i].status_code not in [200, 400, 403, 404]:
            if result[i].status_code == 429:
                speed_too_faster += 1
            elif result[i].status_code == 500:
                server_error_count += 1
            elif result[i].status_code == 504:
                timeout_count += 1
            elif result[i].status_code == 503:
                req_connect_error_count += 1
            else:
                other_count += 1
        else:
            normal_count += 1


    print "并发%s 不同连接总共花的时间是: %s" % (try_time, (d2-d1).total_seconds())
    print "正常的连接数:%s" % normal_count
    print "统计过快的连接数:%s" % speed_too_faster
    print "服务器出错的连接数:%s" % server_error_count
    print "服务相应成功,但请求连接失败的连接数:%s" % req_connect_error_count
    print "超时的的连接数:%s" % timeout_count
    print "服务连接失败的连接数:%s" % connect_error_count
    print "其他错误的连接数:%s" % other_count


same_req()
no_same_req()
