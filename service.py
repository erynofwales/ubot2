# service.py
# Eryn Wells <eryn@erynwells.me>

import logging
import requests

slack = None

class SlackService(object):
    '''Handles requests at the Slack API.'''

    _API_BASE = 'https://slack.com/api'

    def __init__(self, token, host):
        self.token = token
        self.host = host
        self.logger = logging.getLogger('service')

    def permalink(self, channel, message):
        '''
        Generate a permalink to the given message object in the given channel.
        Channel should be the name of the channel, without the leading '#'.
        `message` should have a `ts` field.
        '''
        try:
            ts = message['ts']
        except KeyError:
            return
        ts = ts.replace('.', '')
        return 'https://{}/archives/{}/p{}'.format(self.host, channel, ts)

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

    def remove_pin(self, pin, channel):
        params = self.__params()
        params['channel'] = channel
        if pin['type'] == 'message':
            params['timestamp'] = pin['message']['ts']
        elif pin['type'] == 'file':
            params['file'] = pin['file']['id']
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
            self.logger.info('Response not okay: %s', json['error'])
            return None
        return json
