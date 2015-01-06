#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/29
Desc    :   
"""
from gridfs import GridFS
from gridfs.grid_file import NoFile
from pymongo import Connection
import hashlib
import datetime

import config
from http import HttpInfo
from zip import zip_compress, dezip_compress
from interface import BaseHttpCache


CACHE_CONTROL = 'REQUESTSPOOL.CACHECONTROL'
CACHE_RESULT = 'REQUESTSPOOL.CACHERESULT'


class CACHE_CONTROL_TYPE(object):
    ASYNC_UPDATE = 'async_update'  # 异步强制更新，返回之前的数据
    ASYNC_NOUPDATE = 'async_noupdate'  # 强制不更新，返回之前的数据
    SYNC = 'sync'  # 强制更新，返回新数据
    AUTO = 'auto'  # 默认为auto模式


class CACHE_RESULT_TYPE(object):
    OLD = 'old'  # 旧数据
    NEW = 'new'  # 新数据


def get_mongodb_con(host, port):
    model_name = "mongodb_%s_%s" % (host, port)
    if model_name not in globals():
        db_con = Connection(host=host, port=port)
        globals()[model_name] = db_con
    else:
        db_con = globals()[model_name]
    return db_con


def get_mongodb_db(host, port, db_name, user=None, pw=None):
    model_name = "mongodb_%s_%s_%s" % (host, port, db_name)
    if model_name not in globals():
        db_con = get_mongodb_con(host, port)
        db = db_con[db_name]
        if user:
            try:
                db.authenticate(name=user, password=pw)
            except:
                pass
        globals()[model_name] = db
    else:
        db = globals()[model_name]
    return db


GRIDFS_FIELD_UPLOADDATE = u'uploadDate'
GRIDFS_FIELD_METADATA = u'metadata'
GRIDFS_FIELD_FILEID = u'file_id'
GRIDFS_FIELD_UPDATETIME = u'update_time'
GRIDFS_FIELD_CREATETIME = u'create_time'
GRIDFS_COLL_FILEINFO = u'%s.info' % config.MONGODB_CACHE_COLL_NAME


class MongoGridfsCache(BaseHttpCache):
    def __init__(self):
        self.cache_mongodb = get_mongodb_db(host=config.MONGODB_HOST, port=config.MONGODB_PORT,
                                            db_name=config.MONGODB_DB_NAME,
                                            user=config.MONGODB_USER, pw=config.MONGODB_PW)
        self.file_info_coll = self.cache_mongodb[GRIDFS_COLL_FILEINFO]
        self.gridfs = GridFS(
            self.cache_mongodb,
            config.MONGODB_CACHE_COLL_NAME
        )

    def get_id(self, method, url, req_query_string, req_headers, req_data):
        # 根据请求头hash 取样
        # req_headers不存在或者它为字典
        r_list = [method, url, req_query_string,
                  # TODO request headers 暂不参与缓存id计算 | 注释内容为：将dict key value 直接连接起来
                  # "".join([key + str(val) for key, val in req_headers.iteritems()]) if req_headers else '',
                  req_data if req_data else '']
        return hashlib.sha224("".join(r_list)).hexdigest()

    def delete(self, method, url, req_query_string, req_headers, req_data):
        _id = self.get_id(method, url, req_query_string, req_headers, req_data)
        old = self.file_info_coll.find_one({"_id": _id})
        if old:
            old_file_id = old.get(GRIDFS_FIELD_FILEID)
            self.file_info_coll.remove(_id)
            self.gridfs.delete(old_file_id)
            return True
        return False

    def save(self, method, url, req_query_string, req_headers, req_data, status_code, res_headers, res_data):
        _id = self.get_id(method, url, req_query_string, req_headers, req_data)
        file_id = self.gridfs.put(
            # 压缩存储data
            zip_compress(res_data),
            metadata=HttpInfo(method=method, url=url, req_query_string=req_query_string, req_headers=req_headers,
                              req_data=req_data, res_headers=res_headers, status_code=status_code).dumps()
        )
        old = self.file_info_coll.find_one({"_id": _id})
        now = datetime.datetime.now()
        save_dict = {
            GRIDFS_FIELD_FILEID: file_id,
            GRIDFS_FIELD_UPDATETIME: now,
        }
        if old:
            old_file_id = old.get(GRIDFS_FIELD_FILEID)
            self.file_info_coll.update({"_id": _id}, {"$set": save_dict})
            # 保证可以访问到旧文件
            self.gridfs.delete(old_file_id)
        else:
            save_dict.update({"_id": _id, GRIDFS_FIELD_CREATETIME: now, "url": url})
            self.file_info_coll.save(save_dict)

    def find(self, method, url, req_query_string, req_headers, req_data, **kwargs):
        _id = self.get_id(method, url, req_query_string, req_headers, req_data)
        doc = self.file_info_coll.find_one({'_id': _id}, fields=[GRIDFS_FIELD_FILEID])
        if not doc:
            return None, None
        try:
            gf_item = self.gridfs.get(doc.get(GRIDFS_FIELD_FILEID))
        except NoFile, e:
            return None, None
        url_info = getattr(gf_item, GRIDFS_FIELD_METADATA, None)
        if isinstance(url_info, str) or isinstance(url_info, unicode):
            url_info = HttpInfo.loads(url_info)
        else:
            url_info = None
        # 解压缩
        res_data = dezip_compress(gf_item.read())
        return url_info, res_data


    def get_update_time(self, method, url, req_query_string, req_headers, req_data):
        _id = self.get_id(method, url, req_query_string, req_headers, req_data)
        doc = self.file_info_coll.find_one({'_id': _id}, fields=[GRIDFS_FIELD_UPDATETIME])
        return doc.get(GRIDFS_FIELD_UPDATETIME) if doc else None


if 'CACHE_TYPE' in vars(config) and config.CACHE_TYPE == 'mongodbgridfs':
    cache = MongoGridfsCache()
else:
    raise ValueError(u'尚未配置Cache，请检查config.CACHE_TYPE和相关配置项')