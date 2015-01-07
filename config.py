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

PORT = 8801

CACHE_TYPE = 'mongodbgridfs'
MONGODB_HOST = 'localhost'
MONGODB_PORT = 17117
MONGODB_DB_NAME = 'http_cache'
MONGODB_USER = 'test'
MONGODB_PW = 'test'
MONGODB_CACHE_COLL_NAME = 'cache'

# route规则
ROUTE_MOD = 'route_default'
