# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
import pymongo


class InstaPipeline:
    def process_item(self, item, spider):
        return item


class SaveToMongoPipeline:
    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client["instagram"]

    def process_item(self, item, spider):
        collection = self.db[type(item).__name__.lower()]
        collection.insert_one(item)
        return item


class InstaImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['data'].get('display_url', []):
            yield Request(item['data']['display_url'])

    def item_completed(self, results, item, info):
        if results:
            item['data']['display_url'] = results[0][1]
        return item
