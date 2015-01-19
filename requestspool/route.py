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
from gevent.lock import RLock

from requests import exceptions

from .config import MAX_LOCK_NUM, DEBUG

from interface import BaseRoute, BaseSpeed, BaseUpdate
from http import get_http_result
from cache import cache, CACHE_CONTROL, CACHE_CONTROL_TYPE, CACHE_RESULT, CACHE_RESULT_TYPE
from update import BackendRun
from .util import backend_call


ONESECOND = 1000.0
from . import TIMEOUT_STATUS_CODE
from . import SERVICE_UNAVAILABLE_STATUS_CODE


class TYPE():
    REGEX = 0
    NORMAL = 1


class MultiprocessingValue():
    def __init__(self, _type, default):
        self._value = default

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    value = property(get_value, set_value)


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

    def get_waiting_req(self):
        return self._waiting_req.value

    def set_waiting_req(self, value):
        self._waiting_req.value = value

    # ----------------------------------------------- #

    def __init__(self, limit_req, count_time=ONESECOND):
        # 单位时钟时间，默认1秒，单位毫秒
        self.count_time = count_time
        # 时钟周期内允许的请求数，超过就阻塞请求
        self.limit_req = limit_req

        # timer相关
        self._running = False
        '''
            注册的callback必须不能阻塞的.
            否则timer会不准
        '''
        self._callback = BackendRun()

        self._last_count_time = MultiprocessingValue('d', 0.0)
        self._one_clock_req = MultiprocessingValue('I', 0)
        self._waiting_req = MultiprocessingValue('I', 0)
        self._lock = RLock()

        # 最大同步锁数量
        # 当前正在下载的id上锁,相同的下载全部阻塞
        self._sync_id_default_value = ' '*cache.ID_LENGTH
        lock_count = limit_req if limit_req < MAX_LOCK_NUM else MAX_LOCK_NUM
        self._sync_id_list = [MultiprocessingValue('c', self._sync_id_default_value) for _ in xrange(lock_count)]
        self._sync_lock_list = [RLock() for _ in xrange(lock_count)]
        # 要遍历_sync_id_list,必须上锁,因为_sync_id_list是RawArray
        self._sync_lock_main = RLock()

        # 开始定时后台更新
        self._spawn = backend_call(self.__forever)

    last_count_time = property(get_last_count_time, set_last_count_time)
    one_clock_req = property(get_one_clock_req, set_one_clock_req)
    waiting_req = property(get_waiting_req, set_waiting_req)

    def _reset_clock(self):
        self.last_count_time = time.time()
        self.one_clock_req = 0

    def check_reset(self, now_time):
        return self.one_clock_req >= self.limit_req and \
               (now_time - self.last_count_time) * ONESECOND < self.count_time

    def check_over_time(self, now_time):
        return (now_time - self.last_count_time) * ONESECOND > self.count_time

    def add_one(self):
        self.waiting_req += 1
        with self._lock:
            now = time.time()
            if self.check_reset(now):
                # 当前请求数超过 每个时钟周期 允许的请求数
                gevent.sleep((self.count_time - (now - self.last_count_time) * ONESECOND) / ONESECOND)
                self._reset_clock()
            elif self.check_over_time(now):
                # 长时间未访问
                self._reset_clock()
            self.waiting_req -= 1
            self.one_clock_req += 1

    def add_back_req(self, route, **kwargs):
        self._callback.add(route=route, **kwargs)

    def id_in_lockpool(self, _id):
        for m_array in self._sync_id_list:
            if _id == m_array.value:
                return True
        return False

    def finish_id_lock(self, _id):
        for m_array in self._sync_id_list:
            if _id == m_array.value:
                m_array.value = self._sync_id_default_value

    def get_id_lock(self, _id):
        for i, m_array in enumerate(self._sync_id_list):
            if self._sync_id_default_value == m_array.value:
                m_array.value = _id
                return self._sync_lock_list[i]
            elif _id == m_array.value:
                return self._sync_lock_list[i]

    def get_sync_main_lock(self):
        return self._sync_lock_main

    def __forever(self):
        self._running = True
        per_time_sec = self.count_time * 1.0 / (self.limit_req*1000)
        clock_sec = self.count_time * 1.0 / 1000

        self.last_count_time = time.time()

        while self._running:
            with self._callback:
                # 如果有锁且没有资源,就阻塞
                # 目标请求数
                standard_count = 0

                left_time = time.time() - self.last_count_time
                if left_time < clock_sec:
                    standard_count = int(left_time / per_time_sec)
                elif left_time > clock_sec:
                    # 时钟超时
                    self.one_clock_req = 0
                    standard_count = self.limit_req

                total_now_req = self.one_clock_req + self.waiting_req
                if self._callback and standard_count > total_now_req:
                    # 当前时间标准请求数小于现在请求数,用光现有请求
                    count = standard_count - total_now_req if len(self._callback) > standard_count - total_now_req \
                        else len(self._callback)
                    for _ in xrange(count):
                        self._callback()
                    s_time = per_time_sec
                else:
                    s_time = (total_now_req - standard_count) * per_time_sec \
                        if standard_count < total_now_req else per_time_sec
                # 睡眠到空闲,如果刚好,则睡眠 每次单位连接时间
                gevent.sleep(s_time)



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
        except exceptions.Timeout:
            status_code, res_headers, output = TIMEOUT_STATUS_CODE, {}, ""
        except exceptions.ConnectionError:
            status_code, res_headers, output = SERVICE_UNAVAILABLE_STATUS_CODE, {}, ""
        self.finish_req()
        return status_code, res_headers, output

    def _call_http_request(self, url, method, req_data=None, req_headers=None, req_query_string=None, **kwargs):
        # 失败重试
        # 储存符合的结果到缓存中
        req_kwargs = dict(
            url=url, method=method, req_headers=req_headers, req_data=req_data, req_query_string=req_query_string,
            # 设置请求超时
            timeout=self._update.requests_timeout if self._update and self._update.requests_timeout else None,
            **kwargs)
        status_code, res_headers, output = self._get_http_result(**req_kwargs)
        if self._update:
            save_dict = dict(method=method, url=url, req_query_string=req_query_string, req_headers=req_headers,
                             req_data=req_data, status_code=status_code, res_headers=res_headers, res_data=output)
            if self._update.retry_check_callback and self._update.retry_check_callback(**save_dict):
                # 符合重试条件
                for retry_count in xrange(self._update.retry_limit):
                    # 重新发起连接
                    status_code, res_headers, output = self._get_http_result(**req_kwargs)
                    save_dict.update(dict(status_code=status_code, res_headers=res_headers, res_data=output))
                    if status_code == TIMEOUT_STATUS_CODE:
                        # 继续重试
                        continue
                    if not self._update.retry_check_callback(**save_dict):
                        # 不再需要重试
                        break
            # status_code == TIMEOUT_STATUS_CODE 请求超时
            if status_code != TIMEOUT_STATUS_CODE and (not self._update.save_check_callback or
                (self._update.save_check_callback and self._update.save_check_callback(**save_dict))):
                # 需要缓存
                cache.save(**save_dict)
        return status_code, res_headers, output

    def call_http_request(self, **kwargs):
        # 锁处理
        if self._speed:
            # 存在speed控制
            _id = cache.get_id(**kwargs)
            _lock = None
            _sync = None
            with self._speed.get_sync_main_lock():
                if self._speed.id_in_lockpool(_id):
                    _sync = False
                else:
                    _sync = True
                _lock = self._speed.get_id_lock(_id)

            if _lock is not None and _sync is not None:
                # 有空余的锁
                if _sync:
                    # 同步处理,其他相同链接进入等待
                    with _lock:
                        result = self._call_http_request(**kwargs)
                        with self._speed.get_sync_main_lock():
                            # 释放锁空间
                            self._speed.finish_id_lock(_id)
                        return result

                else:
                    with _lock:
                        # 等待其他连接处理完成
                        pass
                    _, is_in_cache = self._update.is_expired_incache(**kwargs)
                    if is_in_cache:
                        # 其他连接储存了缓存
                        url_info, res_data = cache.find(**kwargs)
                        return url_info.status_code, url_info.res_headers, res_data
        return self._call_http_request(**kwargs)

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

    def add_back_req(self, **kwargs):
        if self._speed:
            self._speed.add_back_req(route=self, **kwargs)
        else:
            backend_call(self.call_http_request, **kwargs)

    '''
        requestpool_headers : 项目控制所需的header,当出现在这里时不会出现在普通request headers
        注意,同步取数据的保存数据不能异步,保证后面锁住的其他客户可以从缓存中拿到数据
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
                    self.add_back_req(**kwargs)
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
                    self.add_back_req(**kwargs)
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
