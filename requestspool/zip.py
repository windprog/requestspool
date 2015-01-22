#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/29
Desc    :   数据压缩
"""
import StringIO
import gzip
import zlib


def ungzip_compress(_str):
    # http gzip压缩解压
    compressed_stream = StringIO.StringIO(_str)
    gzipper = gzip.GzipFile(fileobj=compressed_stream)
    return gzipper.read()


def dezip_compress(_str):
    return zlib.decompress(_str)


def zip_compress(_str):
    return zlib.compress(_str)
