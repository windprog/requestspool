#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   路由,具体实现需要继承interface.BaseSpeed

外部缓存控制,需要添加请求头:
key      : REQUESTPOOL.CACHECONTROL
value    :
    * async_update    异步强制更新，返回之前的数据
    * async_noupdate  强制不更新，返回之前的数据
    * sync            强制更新，返回新数据
    * auto            默认为auto模式

"""
import re
import time
import gevent
import multiprocessing
from requests import exceptions

from interface import BaseRoute, BaseSpeed, BaseUpdate
from http import get_http_result
from cache import cache, CACHE_CONTROL, CACHE_CONTROL_TYPE, CACHE_RESULT, CACHE_RESULT_TYPE


ONESECOND = 1000.0
TIMEOUT_STATUS_CODE = -1


class TYPE():
    REGEX = 0
    NORMAL = 1


class Speed(BaseSpeed):
    # 速度控制器

    # -----------------getter setter----------------- #
    def get_last_count_time(self):
        return self._last_count_time.value

    def set_last_count_time(self, value):
        self._last_count_time.value = value

    def get_one_clock_req(self):
        return self._one_clock_req.value

    def set_one_clock_req(self, value):
        self._one_clock_req.value = value

    # ----------------------------------------------- #

    def __init__(self, limit_req, count_time=ONESECOND):
        # 单位时钟时间，默认1秒，单位毫秒
        self.count_time = count_time
        # 时钟周期内允许的请求数，超过就阻塞请求
        self.limit_req = limit_req

        self._last_count_time = multiprocessing.Value('d', 0.0)
        self._one_clock_req = multiprocessing.Value('I', 0)
        self._lock = multiprocessing.Lock()

    last_count_time = property(get_last_count_time, set_last_count_time)
    one_clock_req = property(get_one_clock_req, set_one_clock_req)

    def _reset_clock(self):
        self.last_count_time = time.time()
        self.one_clock_req = 0

    def check_reset(self, now_time):
        return self.one_clock_req >= self.limit_req and \
               (now_time - self.last_count_time) * ONESECOND < self.count_time

    def check_over_time(self, now_time):
        return (now_time - self.last_count_time) * ONESECOND > self.count_time

    def add_one(self):
        with self._lock:
            now = time.time()
            if self.check_reset(now):
                # 当前请求数超过 每个时钟周期 允许的请求数
                gevent.sleep((self.count_time - (now - self.last_count_time) * ONESECOND) / ONESECOND)
                self._reset_clock()
            elif self.check_over_time(now):
                # 长时间未访问
                self._reset_clock()
            self.one_clock_req += 1


class SpeedRoute(BaseRoute):
    def __init__(self, _type, speed=None, update=None, value=None):
        self._type = _type
        self._value = value
        if speed:
            if not isinstance(speed, BaseSpeed):
                raise ValueError('speed must be BaseSpeed subclass instance')
        self._speed = speed
        if update:
            if not isinstance(update, BaseUpdate):
                raise ValueError('update must be BaseUpdate subclass instance')
        self._update = update

    def add_req(self):
        if self._speed:
            self._speed.add_one()

    def finish_req(self):
        pass

    def _get_http_result(self, url, method, req_data=None, req_headers=None, req_query_string=None, **kwargs):
        # 发起http请求
        self.add_req()
        # 发起http request
        try:
            status_code, res_headers, output = get_http_result(url=url, method=method, req_headers=req_headers,
                                                               req_data=req_data, req_query_string=req_query_string,
                                                               **kwargs)
        except exceptions.Timeout, e:
            status_code, res_headers, output = TIMEOUT_STATUS_CODE, {}, ""
        self.finish_req()
        return status_code, res_headers, output

    def call_http_request(self, url, method, req_data=None, req_headers=None, req_query_string=None, **kwargs):
        # 失败重试
        # 储存符合的结果到缓存中
        status_code, res_headers, output = self._get_http_result(
            url=url, method=method, req_headers=req_headers, req_data=req_data, req_query_string=req_query_string,
            timeout=self._update.requests_timeout if self._update else None,  # 设置请求超时
            **kwargs)
        if self._update:
            save_dict = dict(method=method, url=url, req_query_string=req_query_string, req_headers=req_headers,
                             req_data=req_data, status_code=status_code, res_headers=res_headers, res_data=output)
            # status_code == TIMEOUT_STATUS_CODE 请求超时
            if self._update.retry_check_callback and \
                    (status_code == TIMEOUT_STATUS_CODE or self._update.retry_check_callback(**save_dict)):
                # 符合重试条件
                for retry_count in xrange(self._update.retry_limit):
                    # 重新发起连接
                    status_code, res_headers, output = self._get_http_result(
                        url=url, method=method, req_headers=req_headers,
                        req_data=req_data, req_query_string=req_query_string,
                        timeout=self._update.requests_timeout if self._update else None,  # 设置请求超时
                        **kwargs)
                    save_dict.update(dict(status_code=status_code, res_headers=res_headers, res_data=output))
                    if status_code == TIMEOUT_STATUS_CODE:
                        # 继续重试
                        continue
                    if not self._update.retry_check_callback(**save_dict):
                        # 不再需要重试
                        break

            if not self._update.save_check_callback or \
                    (self._update.save_check_callback and self._update.save_check_callback(**save_dict)):
                # 需要缓存
                cache.save(**save_dict)
        return status_code, res_headers, output

    @staticmethod
    def parse_nocache_res(status_code, res_headers, res_data):
        if hasattr(res_headers, "__setitem__"):
            res_headers[CACHE_RESULT] = CACHE_RESULT_TYPE.NEW
        return status_code, res_headers, res_data

    @staticmethod
    def parse_cache_res(url_info, res_data):
        if hasattr(url_info.res_headers, "__setitem__"):
            url_info.res_headers[CACHE_RESULT] = CACHE_RESULT_TYPE.OLD
        return url_info.status_code, url_info.res_headers, res_data

    '''
        requestpool_headers : 项目控制所需的header,当出现在这里时不会出现在普通request headers
    '''

    def http_result(self, requestpool_headers=None, **kwargs):
        # 判断缓存条件
        if not self._update:
            # 没有缓存配置，不保存缓存
            return self.parse_nocache_res(*self.call_http_request(**kwargs))
        is_expired, is_in_cache = self._update.is_expired_incache(**kwargs)
        if is_in_cache:
            # 存在缓存
            # 外部控制
            if requestpool_headers and CACHE_CONTROL in requestpool_headers:
                requestpool_cache_control = requestpool_headers.get(CACHE_CONTROL)
                if requestpool_cache_control == CACHE_CONTROL_TYPE.ASYNC_UPDATE:
                    # 异步获取
                    self._update.backend_call(self, **kwargs)
                    return self.parse_cache_res(*cache.find(**kwargs))
                elif requestpool_cache_control == CACHE_CONTROL_TYPE.ASYNC_NOUPDATE:
                    return self.parse_cache_res(*cache.find(**kwargs))
                elif requestpool_cache_control == CACHE_CONTROL_TYPE.SYNC:
                    # 强制更新
                    return self.parse_nocache_res(*self.call_http_request(**kwargs))

            # 自动控制
            if is_expired:
                # 超出缓存时间
                if not self._update.check_sync():
                    # 异步取，拿旧数据
                    self._update.backend_call(self, **kwargs)
                    return self.parse_cache_res(*cache.find(**kwargs))
                else:
                    # 同步获取
                    return self.parse_nocache_res(*self.call_http_request(**kwargs))
            else:
                # 在缓存周期内，不发起http 请求，直接取缓存。
                return self.parse_cache_res(*cache.find(**kwargs))
        else:
            return self.parse_nocache_res(*self.call_http_request(**kwargs))


class NormalRoute(SpeedRoute):
    def __init__(self, value, _type=TYPE.NORMAL, **kwargs):
        super(NormalRoute, self).__init__(value=value, _type=_type, **kwargs)

    def match(self, url):
        # flask style url match
        # todo 尚未实现
        pass


class RegexRoute(SpeedRoute):
    def __init__(self, pattern, flags=0, **kwargs):
        super(RegexRoute, self).__init__(_type=TYPE.REGEX, **kwargs)
        self._value = re.compile(pattern, flags=flags)
        self._pattern = pattern
        self._flags = flags

    def match(self, url):
        return self._value.match(url)
