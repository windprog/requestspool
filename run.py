#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/26
Desc    :   
"""
import os
from httpappengine.util import run_server

os.environ.setdefault("APPENGINE_SETTINGS_MODULE", "requestspool.config")

if __name__ == '__main__':
    run_server()
