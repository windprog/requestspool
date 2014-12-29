#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   详细配置说明请参考httpappengine/engine/config.py
"""
DEBUG = True

# 服务器监听地址。
HOST = "0.0.0.0"
PORT = 8801

# 需要载入的Action 模块
ACTIONS = [
    "action",
]

from requestspool.route import RegexRoute, Speed
ROUTE_URL = [
    # 每秒
    RegexRoute(pattern=u".*?/soccer/get_", speed=Speed(count_time=1000*10, limit_req=100)),
    RegexRoute(pattern=u"http://www.baidu.com.*", speed=Speed(count_time=1000*10, limit_req=100)),
]