# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class Vacancy(Item):
    _id = Field()
    url = Field()
    title = Field()
    salary = Field()
    description = Field()
    skills = Field()
    employer = Field()
    employer_url = Field()


class Employer(Item):
    _id = Field()
    name = Field()
    site = Field()
    business_fields = Field()
    description = Field()
    url = Field()
