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
ADD_RE = None

COLLECTIONS = {}

#
# rtmbot interface
#

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

    collections_re = '|'.join(COLLECTIONS.keys())
    collections_re = r'(?P<collection>{})'.format(collections_re)
    global CMD_RE
    CMD_RE = re.compile(r'!{}(\s+(me|(?P<count>\d+)))?'.format(collections_re))
    ADD_RE = re.compile(r'!bombadd\s+{}\s+(?P<item>\S+)'.format(collections_re))

def process_message(data):
    try:
        text = data['text']
    except KeyError:
        LOGGER.error('Missing "text" key in data.')
        return

    match = CMD_RE.match(text)
    if match:
        _handle_bomb(match, data['channel'])
    match = ADD_RE.match(text)
    if match:
        _handle_add(match, data['channel'])

#
# Bomb bomb bomb
#

def _handle_bomb(match, channel):
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
        outputs.append([channel, i])

def _handle_add(match, channel):
    collection = match.group('collection')
    item = match.group('item')
    LOGGER.debug('Adding item to %s: %s', collection, item)
    COLLECTIONS[collection].append(item)
    _dump_collection(collection, COLLECTIONS[collection])
    outputs.append([channel, '_Saved {} to {} collection_'.format(item, collection)])

def _dump_collection(collection, items):
    LOGGER.info('Saving collection %s: %d item%s', collection, 's' if len(items) != 1 else '')
    filename = 'bomb.{}.json'.format(collection)
    with open(filename, 'w') as f:
        json.dump(f, items)

