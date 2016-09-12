# service.py
# Eryn Wells <eryn@erynwells.me>

import requests

slack = None

class SlackService(object):
    '''Handles requests at the Slack API.'''

    _API_BASE = 'https://slack.com/api'

    def __init__(self, token):
        self.token = token

    #
    # Endpoints
    #

    def channels(self):
        params = self.__params()
        r = requests.get(self.__url('channels.list'), params=params)
        json = self.__extract_json(r)
        return json['channels'] if json else None

    def pins(self, channel):
        params = self.__params(channel=channel)
        r = requests.get(self.__url('pins.list'), params=params)
        json = self.__extract_json(r)
        return json['items'] if json else None

    def remove_pin(self, pin):
        params = self.__params()
        if pin['type'] == 'message':
            params['channel'] = pin['channel']
            params['timestamp'] = pin['message']['ts']
        r = requests.get(self.__url('pins.remove'), params=params)
        json = self.__extract_json(r)
        return json is not None

    def users(self):
        params = self.__params()
        r = requests.get(self.__url('users.list'), params=params)
        json = self.__extract_json(r)
        return json['members'] if json else None

    #
    # Private
    #

    def __url(self, verb):
        return SlackService._API_BASE + '/' + verb

    def __params(self, **kwargs):
        self.__append_token_param(kwargs)
        return kwargs

    def __append_token_param(self, params):
        params['token'] = self.token

    def __extract_json(self, response, code=200):
        if response.status_code != code:
            return None
        json = response.json()
        if not json['ok']:
            return None
        return json
