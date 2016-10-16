# pugz.py
# Needs moar dogos
# Eryn Wells <eryn@erynwells.me>

import json
import glob
import logging
import os.path
import random
import re

LOGGER = logging.getLogger(__name__)
CMD_RE = None

COLLECTIONS = {}

# rtmbot interface
outputs = []

def process_hello(data):
    bomb_collections = glob.glob('bomb.*.json')
    LOGGER.info('Found some bomb collections: %s', bomb_collections)

    global COLLECTIONS
    COLLECTIONS = {}
    for c in bomb_collections:
        base = os.path.basename(c)
        parts = base.split('.')
        LOGGER.info('Loading collection %s: %s', parts[1], c)
        with open(c, 'r') as f:
            COLLECTIONS[parts[1]] = json.load(f)

    collection_commands_re = '|'.join(COLLECTIONS.keys())
    collection_commands_re = r'(?P<collection>{})'.format(collection_commands_re)
    global CMD_RE
    CMD_RE = re.compile(r'!{}(\s+(me|(?P<count>\d+)))?'.format(collection_commands_re))

def process_message(data):
    try:
        text = data['text']
    except KeyError:
        LOGGER.error('Missing "text" key in data.')
        return

    match = CMD_RE.match(text)
    if not match:
        return

    collection = match.group('collection')

    count = match.group('count')
    try:
        count = int(count)
    except ValueError:  # count isn't an int
        count = 3
    except TypeError:   # count is None
        count = 1

    LOGGER.info('Getting %d item%s from %s', count, '' if count == 1 else 's', collection)
    items = random.sample(COLLECTIONS[collection], count)
    LOGGER.debug('I HAVE BOMB FOOD: %s', items)

    for i in items:
        outputs.append([data['channel'], i])
