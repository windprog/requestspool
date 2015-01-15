#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14/12/29
Desc    :   缓存,具体实现需要继承interface.BaseHttpCache
"""
from gridfs import GridFS
from gridfs.grid_file import NoFile
from pymongo import Connection
import datetime

from . import config
from http import HttpInfo, get_HttpInfo_class
from zip import zip_compress, dezip_compress
from interface import BaseHttpCache


CACHE_CONTROL = 'REQUESTSPOOL.CACHECONTROL'
CACHE_RESULT = 'REQUESTSPOOL.CACHERESULT'

# 配置get_id版本
default_get_id = get_HttpInfo_class(config.DEFAULT_HTTPINFO_VERSION).get_id


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


GRIDFS_FIELD_METADATA = u'metadata'
GRIDFS_FIELD_FILEID = u'file_id'
GRIDFS_FIELD_UPDATETIME = u'update_time'
GRIDFS_FIELD_CREATETIME = u'create_time'
GRIDFS_FIELD_HTTPINFO_VERSION = u"httpinfo_version"
GRIDFS_COLL_FILEINFO = u'%s.info' % config.MONGODB_CACHE_COLL_NAME
GRIDFS_COLL_FILES = u'%s.files' % config.MONGODB_CACHE_COLL_NAME


class MongoGridfsCache(BaseHttpCache):
    def __init__(self):
        self.cache_mongodb = get_mongodb_db(host=config.MONGODB_HOST, port=config.MONGODB_PORT,
                                            db_name=config.MONGODB_DB_NAME,
                                            user=config.MONGODB_USER, pw=config.MONGODB_PW)
        # 储存创建时间等基本信息
        self.file_info_coll = self.cache_mongodb[GRIDFS_COLL_FILEINFO]
        # gridfs自带,内有checksum等信息
        self.file_files_coll = self.cache_mongodb[GRIDFS_COLL_FILES]
        self.gridfs = GridFS(
            self.cache_mongodb,
            config.MONGODB_CACHE_COLL_NAME
        )

    @staticmethod
    def get_id(method, url, req_query_string, req_headers, req_data):
        # 默认获取id方式
        return default_get_id(method, url, req_query_string, req_headers, req_data)

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
            GRIDFS_FIELD_HTTPINFO_VERSION: config.DEFAULT_HTTPINFO_VERSION,
        }
        if old:
            old_file_id = old.get(GRIDFS_FIELD_FILEID)
            self.file_info_coll.update({"_id": _id}, {"$set": save_dict})
            # 保证可以访问到旧文件
            self.gridfs.delete(old_file_id)
        else:
            save_dict.update({"_id": _id, GRIDFS_FIELD_CREATETIME: now, "url": url})
            self.file_info_coll.save(save_dict)

    def find_httpinfo(self, method, url, req_query_string, req_headers, req_data, **kwargs):
        _id = self.get_id(method, url, req_query_string, req_headers, req_data)
        # 检查数据是否存在,拿到httpinfo version
        doc = self.file_info_coll.find_one({'_id': _id}, fields=[GRIDFS_FIELD_FILEID, GRIDFS_FIELD_HTTPINFO_VERSION])
        if doc:
            # 获取metadata
            r = self.file_files_coll.find_one({'_id': doc.get(GRIDFS_FIELD_FILEID)}, fields=[GRIDFS_FIELD_METADATA])
            metadata = r.get(GRIDFS_FIELD_METADATA)
            version = doc.get(GRIDFS_FIELD_HTTPINFO_VERSION)
            if version != config.DEFAULT_HTTPINFO_VERSION:
                return get_HttpInfo_class(version).loads(metadata) if isinstance(metadata, basestring) else None
            return HttpInfo.loads(metadata) if isinstance(metadata, basestring) else None

    def find(self, method, url, req_query_string, req_headers, req_data, **kwargs):
        _id = self.get_id(method, url, req_query_string, req_headers, req_data)
        doc = self.file_info_coll.find_one({'_id': _id}, fields=[GRIDFS_FIELD_FILEID, GRIDFS_FIELD_HTTPINFO_VERSION])
        if not doc:
            return None, None
        try:
            gf_item = self.gridfs.get(doc.get(GRIDFS_FIELD_FILEID))
        except NoFile, e:
            return None, None
        metadata = getattr(gf_item, GRIDFS_FIELD_METADATA, None)
        version = doc.get(GRIDFS_FIELD_HTTPINFO_VERSION)
        if version == config.DEFAULT_HTTPINFO_VERSION:
            url_info = HttpInfo.loads(metadata) if isinstance(metadata, basestring) else None
        else:
            url_info = get_HttpInfo_class(version).loads(metadata) if isinstance(metadata, basestring) else None
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