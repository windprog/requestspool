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


route = [
    # 执行测试用例需要用到百度
    # 百度每10秒访问一次, 20秒缓存过期
    RegexRoute(pattern=u"http://www.baidu.com.*", speed=Speed(count_time=1000 * 10, limit_req=1), update=Update(20, True)),
    # 代理请求
    RegexRoute(pattern=u".*"),
]
