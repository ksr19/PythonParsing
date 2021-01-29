# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo
import os
from dotenv import load_dotenv
from scrapy.settings import Settings


class GbParsePipeline:

    def __init__(self):
        crawler_settings = Settings()
        crawler_settings.setmodule('gb_parse.settings')
        load_dotenv("../.env")
        data_base_url = os.getenv("DATA_BASE_URL")
        self.connection = pymongo.MongoClient(data_base_url)
        db = self.connection[crawler_settings['MONGODB_DB']]
        self.collection = db[crawler_settings['MONGODB_COLLECTION']]

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        self.collection.insert(dict(item))
        return item
