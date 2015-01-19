#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   
"""
from gevent import monkey
monkey.patch_all()
import os
from httpappengine.util import run_server

os.environ.setdefault("APPENGINE_SETTINGS_MODULE", "requestspool.config")

run_server()