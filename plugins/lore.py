# cookie.py
# Pin management
# Eryn Wells <eryn@erynwells.me>

import json
import logging
import random
import re

import requests

from service import slack

LOGGER = logging.getLogger('cookie')
MAX_PINS = 100
LORE_FILE = 'lore.json'
CHANNELS = {}
ANGER_MESSAGES = [':anger:', ':angry:']

LORE_RE = re.compile(r'!lore\s+(?P<count>\d+)')
SCRIBE_RE = re.compile(r'!scribe\s+(?P<message>.*)')

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
        return 'lore.json'

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

    m = LORE_RE.match(text)
    if m:
        try:
            chid = data['channel']
            ch = CHANNELS[chid]
            lore = _lore(ch, int(m.group('count')))
            if lore:
                for l in lore:
                    outputs.append([chid, l])
            return
        except KeyError as e:
            LOGGER.error("Couldn't process !lore command: {}".format(e))

    m = SCRIBE_RE.match(text)
    if m:
        _scribe()

#
# Private
#

def _lore(channel, count):
    pins = channel.saved_pins
    if not pins:
        return None
    if len(pins) < count:
        return [_extract_lore(p) for p in pins]
    out_lore = set()
    while len(out_lore) < count:
        random_lore = random.choice(pins)
        lore = _extract_lore(random_lore)
        out_lore.add(lore)
    return out_lore

def _scribe():
    LOGGER.error('!scribe not implemented yet :-(')
    pass

def _extract_lore(obj):
    if obj['type'] == 'message':
        return obj['message']['permalink']
    elif obj['type'] == 'file':
        return obj['file']['permalink']
    # If nothing matches just return the object itself as a preformatted JSON object
    return '```\n' + json.dumps(obj, indent=2) + '\n```'
