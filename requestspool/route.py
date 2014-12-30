#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :

外部请求头
requestpool.cachecontrol
    * async_update    异步强制更新，返回之前的数据
    * async_noupdate  强制不更新，返回之前的数据
    * sync            强制更新，返回新数据
    * auto            默认为auto模式

"""
import re
import time
import gevent
import multiprocessing

from interface import BaseRoute, BaseSpeed, BaseUpdate
from http import get_http_result
from requestspool.cache import cache, CACHE_CONTROL, CACHE_CONTROL_TYPE


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

    def check_over_time(self, now_time):
        return (now_time - self._last_count_time.value) * ONESECOND > self.count_time

    def add_one(self):
        with self._lock:
            now = time.time()
            if self.check_reset(now):
                # 当前请求数超过 每个时钟周期 允许的请求数
                gevent.sleep((self.count_time - (now - self._last_count_time.value) * ONESECOND) / ONESECOND)
                self._reset_clock()
            elif self.check_over_time(now):
                self._reset_clock()
            self._one_clock_req.value += 1


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
                raise ValueError('speed must be BaseUpdate subclass instance')
        self._update = update

    def add_req(self):
        if self._speed:
            self._speed.add_one()

    def finish_req(self):
        pass

    def call_http_request(self, url, method, req_data=None, req_headers=None, req_query_string=None, **kwargs):
        # 失败重试#
        # 缓存成功条件
        self.add_req()
        try:
            # 发起http request
            status_code, headers, output = get_http_result(url=url, method=method, req_headers=req_headers,
                                                           req_data=req_data, req_query_string=req_query_string,
                                                           **kwargs)
            if self._update:

                save_dict = dict(method=method, url=url, req_query_string=req_query_string, req_headers=req_headers,
                                 req_data=req_data, status_code=status_code, res_headers=headers, res_data=output)
                if self._update.retry_check_callback and self._update.retry_check_callback(**save_dict):
                    # 符合重试条件
                    for retry_count in xrange(self._update.retry_limit):
                        # 重新发起连接
                        self.add_req()
                        try:
                            status_code, headers, output = get_http_result(url=url, method=method,
                                                                           req_headers=req_headers, req_data=req_data,
                                                                           req_query_string=req_query_string, **kwargs)
                        except:
                            # 下载失败，可呢过是由于parse_requests_result函数处理出错
                            pass
                        finally:
                            self.finish_req()
                        save_dict.update(dict(status_code=status_code, res_headers=headers, res_data=output))
                        if not self._update.retry_check_callback(**save_dict):
                            # 不再需要重试
                            break

                if not self._update.save_check_callback or \
                        (self._update.save_check_callback and self._update.save_check_callback(**save_dict)):
                    # 需要缓存
                    cache.save(**save_dict)
            else:
                # 没有缓存管理，每次都拿新数据
                pass
            return status_code, headers, output
        except:
            pass
        finally:
            self.finish_req()

    def get_http_result(self, requestpool_headers=None, **kwargs):
        # 添加连接，满足条件会阻塞执行
        if not self._update:
            # 没有缓存配置，不保存缓存
            return self.call_http_request(**kwargs)
        is_expired, is_in_cache = self._update.get_expired_bool(**kwargs)
        if is_in_cache:
            # 外部控制
            if requestpool_headers and CACHE_CONTROL in requestpool_headers:
                requestpool_cache_control = requestpool_headers.get(CACHE_CONTROL)
                if requestpool_cache_control == CACHE_CONTROL_TYPE.ASYNC_UPDATE:
                    # 异步获取
                    self._update.backend_call(**kwargs)
                    url_info, res_data = cache.find(**kwargs)
                    return url_info.status_code, url_info.req_headers, res_data
                elif requestpool_cache_control == CACHE_CONTROL_TYPE.ASYNC_NOUPDATE:
                    url_info, res_data = cache.find(**kwargs)
                    return url_info.status_code, url_info.req_headers, res_data
                elif requestpool_cache_control == CACHE_CONTROL_TYPE.SYNC:
                    # 强制更新
                    return self.call_http_request(**kwargs)

            # 存在缓存
            if is_expired:
                # 超出缓存时间
                if not self._update.check_sync():
                    # 异步获取
                    self._update.backend_call(**kwargs)
                    url_info, res_data = cache.find(**kwargs)
                    return url_info.status_code, url_info.req_headers, res_data
                else:
                    # 同步获取
                    return self.call_http_request(**kwargs)
            else:
                # 在缓存周期内，不发起http 请求，直接取缓存。
                url_info, res_data = cache.find(**kwargs)
                return url_info.status_code, url_info.req_headers, res_data
        else:
            return self.call_http_request(**kwargs)


class NormalRoute(SpeedRoute):
    def __init__(self, value, _type=TYPE.NORMAL, **kwargs):
        super(NormalRoute, self).__init__(value=value, _type=_type, **kwargs)

    def match(self, url):
        # flask format url match
        # todo 尚未实现
        pass


class RegexRoute(SpeedRoute):
    def __init__(self, pattern, flags=0, **kwargs):
        super(RegexRoute, self).__init__(_type=TYPE.REGEX, **kwargs)
        self._value = re.compile(pattern, flags=flags)

    def match(self, url):
        return self._value.match(url)