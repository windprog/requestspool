#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   15/1/6
Desc    :   
"""
from requestspool.route import RegexRoute, Speed
from requestspool.update import Update
from requestspool.interface import BaseCheckCallback
from requestspool import TIMEOUT_STATUS_CODE


class SWSaveCheckCallBack(BaseCheckCallback):
    def __call__(self, status_code, **kwargs):
        return status_code != 302


class SWRetryCheckCallBack(BaseCheckCallback):
    def __call__(self, method, url, req_query_string, req_headers, req_data, status_code, res_headers, res_data):
        if status_code == TIMEOUT_STATUS_CODE:
            # 请求超时,进行重试
            self.sleep(10)
            return True
        return False

route = [
    # 执行测试用例需要用到百度
    # 百度每10秒访问一次, 20秒缓存过期
    RegexRoute(pattern=u"http://www.baidu.com.*", speed=Speed(count_time=1000 * 10, limit_req=1), update=Update(20, False)),
    # 代理请求
    RegexRoute(pattern=u".*"),
]
