import scrapy
import json
import datetime as dt
import re
from ..items import FollowUser, TargetUser


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    query_hash = {
        'followers': '5aefa9893005572d237da5068082d8d5',
        'following': '3dec7e2c57367ef3da3d987d89f9dbc8',
    }

    def __init__(self, login, password, *args, **kwargs):
        self.login = login
        self.password = password
        self.users = ['jensonbutton', 'financialtimes', 'ringer', 'wsj', 'neizvestnach']
        super().__init__(*args, **kwargs)
        self.users_ids = {}

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
                for user in self.users:
                    yield response.follow(f'/{user}/', callback=self.user_parse)

    def user_parse(self, response):
        user = self.js_data_extractor(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        variables = self.make_variables(user['id'])
        yield TargetUser(
            {
                'date_parse': dt.datetime.now(),
                'user_id': user['id'],
                'user_name': user['full_name'],
                'data': user,
            }
        )
        yield response.follow(url=f'https://www.instagram.com/graphql/query/?query_hash={self.query_hash["followers"]}'
                                  f'&variables={variables}', callback=self.parse_followers)
        yield response.follow(url=f'https://www.instagram.com/graphql/query/?query_hash={self.query_hash["following"]}'
                                  f'&variables={variables}', callback=self.parse_following)

    def parse_followers(self, response):
        data = response.json()['data']['user']['edge_followed_by']
        followers = data['edges']
        user_parent_id = self.get_user_id(response.url)
        for follower in followers:
            yield self.make_user(user_parent_id, 'Follower', follower)
        if data['page_info']['has_next_page']:
            yield response.follow(
                url=f'https://www.instagram.com/graphql/query/?query_hash={self.query_hash["followers"]}'
                    f'&variables={self.make_variables(user_parent_id, data["page_info"]["end_cursor"])}',
                callback=self.parse_followers)

    def parse_following(self, response):
        data = response.json()['data']['user']['edge_follow']
        following = data['edges']
        user_parent_id = self.get_user_id(response.url)
        for follower in following:
            yield self.make_user(user_parent_id, 'Following', follower)
        if data['page_info']['has_next_page']:
            yield response.follow(
                url=f'https://www.instagram.com/graphql/query/?query_hash={self.query_hash["following"]}'
                    f'&variables={self.make_variables(user_parent_id, data["page_info"]["end_cursor"])}',
                callback=self.parse_following)

    @staticmethod
    def js_data_extractor(response):
        script = response.xpath('//body/script[contains(text(), "csrf_token")]/text()').get()
        return json.loads(script.replace('window._sharedData = ', '', 1)[:-1])

    @staticmethod
    def get_user_id(url):
        pattern = re.compile('22id%22:%20%22(\d*)')
        user_id = re.findall(pattern, url)[0]
        return user_id

    @staticmethod
    def make_variables(_id, end_cursor=None):
        variables = {
            'id': _id,
            'include_reel': True,
            'fetch_mutual': True,
            'first': 24,
        }
        if end_cursor:
            variables.update(
                {
                    'after': end_cursor,
                }
            )
        return json.dumps(variables)

    @staticmethod
    def make_user(_id, _type, _info):
        return FollowUser(
            {
                'date_parse': dt.datetime.now(),
                'user_class': _type,
                'user_parent_id': _id,
                'data': _info['node'],
            }
        )
