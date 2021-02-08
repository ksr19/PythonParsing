import scrapy
import json
import datetime as dt
from ..items import Tag, Post


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    query_hash = '9b498c08113f1e09617a1703c22b2f32'

    def __init__(self, login, password, *args, **kwargs):
        self.login = login
        self.password = password
        self.tags = ['python', 'программирование', 'sports', 'футбол', 'developers']
        super().__init__(*args, **kwargs)

    def parse(self, response, **kwargs):
        try:
            js_data = self.js_data_extractor(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    "username": self.login,
                    "enc_password": self.password,
                },
                headers={
                    "X-CSRFToken": js_data['config']['csrf_token'],
                },
            )
        except AttributeError:
            if response.json().get('authenticated'):
                for tag in self.tags:
                    yield response.follow(f'/explore/tags/{tag}/', callback=self.tag_parse)

    def tag_parse(self, response):
        tag = Tag()
        hashtag = self.js_data_extractor(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
        tag['date_parse'] = dt.datetime.now()
        data = {}
        for key, item in hashtag.items():
            if not key.startswith('edge_'):
                data[key] = item
        tag['data'] = data
        yield tag
        # Предполагаю, что посты, которые на данной странице в топе, встретятся нам в
        # процессе обхода картинок по edge_hashtag_to_media.
        # Иначе нужно расскоментировать строчку 67.
        yield from self.parse_page_posts_and_follow(hashtag, response)

    def parse_page_posts_and_follow(self, hashtag, response):
        # yield from self.post_to_item(hashtag['edge_hashtag_to_top_posts']['edges'])
        yield from self.post_to_item(hashtag['edge_hashtag_to_media']['edges'])
        if hashtag['edge_hashtag_to_media']['page_info']['has_next_page']:
            variables = {
                'tag_name': hashtag['name'],
                'first': 50,
                'after': hashtag['edge_hashtag_to_media']['page_info']['end_cursor'],
            }
            yield response.follow(url=f'https://www.instagram.com/graphql/query/?query_hash={self.query_hash}'
                                      f'&variables={json.dumps(variables)}', callback=self.parse_api_posts)

    @staticmethod
    def post_to_item(posts):
        for post in posts:
            top_post = Post()
            top_post['date_parse'] = dt.datetime.now()
            top_post['data'] = post['node']
            yield top_post

    def parse_api_posts(self, response):
        hashtag = json.loads(response.text)['data']['hashtag']
        yield from self.parse_page_posts_and_follow(hashtag, response)

    @staticmethod
    def js_data_extractor(response):
        script = response.xpath('//body/script[contains(text(), "csrf_token")]/text()').get()
        return json.loads(script.replace('window._sharedData = ', '', 1)[:-1])
