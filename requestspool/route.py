#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   
"""
import re
import time
import gevent
import multiprocessing
from http import call_http_request

from interface import BaseRoute, BaseSpeed


ONESECOND = 1000.0


class TYPE():
    REGEX = 0
    NORMAL = 1


class Speed(BaseSpeed):
    # 速度控制器
    def __init__(self, limit_req, count_time=ONESECOND):
        # 单位时钟时间，默认1秒，单位毫秒
        self.count_time = count_time
        # 时钟周期内允许的请求数，超过就阻塞请求
        self.limit_req = limit_req

        self._last_count_time = multiprocessing.Value('d', 0.0)
        self._one_clock_req = multiprocessing.Value('I', 0)
        self._lock = multiprocessing.Lock()

    def _reset_clock(self):
        self._last_count_time.value = time.time()
        self._one_clock_req.value = 0

    def check_reset(self, now_time):
        return self._one_clock_req.value >= self.limit_req and \
               (now_time - self._last_count_time.value) * ONESECOND < self.count_time

    def add_one(self):
        with self._lock:
            now = time.time()
            if self.check_reset(now):
                # 当前请求数超过 每个时钟周期 允许的请求数
                gevent.sleep((self.count_time - (now - self._last_count_time.value) * ONESECOND)/ONESECOND)
                self._reset_clock()
            self._one_clock_req.value += 1


class SpeedRoute(BaseRoute):
    def __init__(self, value, speed, _type):
        self._type = _type
        self._value = value
        if speed:
            if not isinstance(speed, BaseSpeed):
                raise ValueError('speed must be BaseSpeed subclass instance')
        self._speed = speed

    def add_req(self):
        if self._speed:
            self._speed.add_one()

    def finish_req(self):
        pass

    def call_http_request(self, url, method, data=None, params=None, **kwargs):
        # 添加连接，满足条件会阻塞执行
        self.add_req()
        try:
            return call_http_request(url=url, method=method, data=data, params=params, **kwargs)
        except:
            pass
        finally:
            self.finish_req()

class NormalRoute(SpeedRoute):
    def __init__(self, value, speed=None, _type=TYPE.NORMAL):
        super(NormalRoute, self).__init__(value=value, speed=speed, _type=_type)

    def match(self, url):
        # flask format url match
        # todo 尚未实现
        pass



class RegexRoute(SpeedRoute):
    def __init__(self, pattern, flags=0, **kwargs):
        super(RegexRoute, self).__init__(value=pattern, _type=TYPE.REGEX, **kwargs)
        self._value = re.compile(pattern, flags=flags)

    def match(self, url):
        return self._value.match(url)