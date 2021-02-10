# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class FollowUser(Item):
    _id = Field()
    date_parse = Field()
    user_class = Field()
    user_parent_id = Field()
    data = Field()


class TargetUser(Item):
    _id = Field()
    date_parse = Field()
    user_id = Field()
    user_name = Field()
    data = Field()
