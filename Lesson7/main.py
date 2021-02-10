import os
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from insta.spiders.instagram import InstagramSpider

if __name__ == '__main__':
    load_dotenv('.env')
    crawler_settings = Settings()
    crawler_settings.setmodule('insta.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(InstagramSpider, login=os.getenv('LOGIN'), password=os.getenv('PASSWD'))
    crawler_process.start()
