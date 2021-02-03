# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo


class HhRuPipeline:
    def process_item(self, item, spider):
        return item


class SaveToMongoPipeline:
    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client["hh"]

    def process_item(self, item, spider):
        collection = self.db[type(item).__name__.lower()]
        collection.insert_one(item)
        return item
