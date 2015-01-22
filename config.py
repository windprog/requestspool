#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   详细配置说明请参考httpappengine/engine/config.py
"""
# 速度统计为gevent模块,启用True将会不正常
DEBUG = False

PORT = 8801

# 缓存类型
CACHE_TYPE = 'mongodbgridfs'
# mongodb地址
MONGODB_HOST = 'localhost'
# 端口
MONGODB_PORT = 17117
# 存放缓存的数据库名称
MONGODB_DB_NAME = 'http_cache'
# 用户名
MONGODB_USER = 'test'
# 密码
MONGODB_PW = 'test'
# 存放 gridfs 的 mongodb collection 名称
MONGODB_CACHE_COLL_NAME = 'cache'

# route规则
ROUTE_MOD = 'route_default'
