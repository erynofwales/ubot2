# cookie.py
# Pin management
# Eryn Wells <eryn@erynwells.me>

import json
import logging
import random

import requests

from service import slack

LOGGER = logging.getLogger('cookie')
MAX_PINS = 100
CHANNELS = {}

outputs = []

class Channel(object):
    def __init__(self, json):
        self.ident = json['id']
        self.name = json['name']
        self.pins = None

    @property
    def pretty_name(self):
        return '#' + self.name

    @property
    def pin_file(self):
        return 'pins.{}.json'.format(self.name)

    @property
    def saved_pins(self):
        try:
            with open(self.pin_file, 'r') as f:
                obj = json.load(f)
                return obj
        except FileNotFoundError:
            return None

    @property
    def oldest_pin(self):
        if not self.pins or len(self.pins) == 0:
            return None
        return self.pins[-1]

    def fetch_pins(self):
        pins = slack.pins(self.ident)
        # Newest (highest value timestamp) sorted at the beginning.
        pins.sort(key=lambda it: it['created'], reverse=True)
        self.pins = pins
        return pins

    def unpin_oldest_if_needed(self):
        if not _should_unpin(self.pins):
            return
        oldest_pin = self.oldest_pin
        LOGGER.info('Writing pin to {}'.format(self.pin_file))
        self.save_pin(oldest_pin)
        if oldest_pin['type'] == 'message':
            LOGGER.info('Unpinning oldest message: "{}"'.format(oldest_pin['message']))
        removed = self.remove_pin(oldest_pin)
        return oldest_pin

    def remove_pin(self, pin):
        result = slack.remove_pin(pin)
        return result

    def save_pin(self, pin):
        pins = self.saved_pins
        if pins is None:
            pins = []
        filtered_pins = list(filter(lambda p: p['created'] == pin['created'], pins))
        if len(filtered_pins) > 0:
            LOGGER.info('Message already pinned; skipping')
        pins.append(pin)
        self.write_pins(pins)

    def write_pins(self, pins):
        with open(self.pin_file, 'w') as f:
            json.dump(pins, f, indent=2)

def _channels():
    channels = slack.channels()
    if not channels:
        return None
    channels = [c for c in channels if c['is_member']]
    return channels

def _should_unpin(pins):
    return len(pins) >= MAX_PINS

#
# RTM
#

def process_hello(data):
    LOGGER.info('Hello!')
    channels = _channels()
    LOGGER.info('I am in these channels: {}'.format(', '.join(['#' + c['name'] for c in channels])))
    for c in channels:
        ch = Channel(c)
        CHANNELS[ch.ident] = ch
        ch.fetch_pins()
        LOGGER.info('  {} has {} pins.'.format(ch.pretty_name, len(ch.pins)))
        ch.unpin_oldest_if_needed()

def process_channel_joined(data):
    ch = Channel(data['channel'])
    LOGGER.info('Joined {}'.format(ch.pretty_name))
    CHANNELS[ch.ident] = ch
    ch.fetch_pins()
    ch.unpin_oldest_if_needed()

def process_pin_added(data):
    LOGGER.info('Pin added')
    try:
        ch = CHANNELS[data['channel_id']]
        ch.fetch_pins()
        ch.unpin_oldest_if_needed()
    except KeyError as e:
        LOGGER.error("Couldn't get channel for id {}: {}".format(data['channel_id'], e))

def process_message(data):
    try:
        text = data['text'].strip()
    except KeyError as e:
        LOGGER.error("Couldn't extract text from message event: {}".format(e))
        LOGGER.debug(json.dumps(data, indent=2))
        return

    LOGGER.debug('Received message: {}'.format(text))

    if text == '!lore':
        try:
            chid = data['channel']
            ch = CHANNELS[chid]
            random_pin = _lore(ch)
            if random_pin:
                outputs.append([chid, random_pin])
        except KeyError as e:
            LOGGER.error("Couldn't process !lore command: {}".format(e))

#
# Private
#

def _lore(channel):
    pins = channel.saved_pins
    if not pins:
        return None
    random_pin = random.choice(pins)
    if random_pin['type'] == 'message':
        return random_pin['message']['permalink']
    return '```\n' + str(random_pin) + '\n```'
