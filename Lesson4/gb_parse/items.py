# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class GbParseItem(Item):
    user = Field()
    title = Field()
    description = Field()
    specs = Field()
    price = Field()
    photos = Field()
    phones = Field()
