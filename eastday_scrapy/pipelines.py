# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import requests
import hashlib


class EastdayScrapyPipeline(object):
    def process_item(self, item, spider):
        return item


class MongoPipeline(object):
    '''
    保存数据到mongodb
    :param response:
    :return:
    '''

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[item.table_name].update({'title': item.get('title')}, {'$pushAll': {'images': item.get('images')}}, True)
        return item

class SaveFliePileline(object):
    '''
    根据图片链接下载图片
    :param response:
    :return:
    '''
    def process_item(self, item, spider):
        for image in item.get('images'):
            image_response = requests.get(image)
            file_path = '{0}.{1}'.format(hashlib.md5(image_response.content).hexdigest(), 'jpg')
            with open(file_path, 'wb') as f:
                f.write(image_response.content)
        return item