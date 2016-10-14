# pugz.py
# Needs moar dogos
# Eryn Wells <eryn@erynwells.me>

import json
import logging
import re
import requests

LOGGER = logging.getLogger(__name__)
PUG_RE = re.compile(r'!pug(\s+(me|(?P<count>\d+)))?')

PUGS_COUNT_URL = 'http://pugme.herokuapp.com/count'
PUGS_BOMB_URL = 'http://pugme.herokuapp.com/bomb'
PUGS_RANDOM_URL = 'http://pugme.herokuapp.com/random'

MAX_MAX_PUGS = 30   # :sweat_smile:
MAX_PUGS = -1

# rtmbot interface
outputs = []

def process_hello(data):
    global MAX_PUGS

    r = requests.get(PUGS_COUNT_URL)
    if r.status_code != 200:
        MAX_PUGS = MAX_MAX_PUGS
    else:
        json = r.json()
        count = json.get('pug_count', MAX_MAX_PUGS)
        MAX_PUGS = count
    LOGGER.info('Maximum pugs: %d', MAX_PUGS)

def process_message(data):
    try:
        text = data['text']
    except KeyError:
        LOGGER.error('Missing "text" key in data.')
        return

    match = PUG_RE.match(text)
    if not match:
        return

    pugs = []

    count = match.group('count')
    if not count:
        LOGGER.info('Getting random pug')
        r = _get(PUGS_RANDOM_URL)
        pug = r.get('pug')
        if pug:
            pugs.append(pug)
    else:
        try:
            count = int(count)
        except ValueError:
            count = 1
        LOGGER.info('Getting %d pug%s', count, '' if count == 1 else 's')
        r = _get(PUGS_BOMB_URL, count=count)
        pugs = r.get('pugs', [])
        LOGGER.debug('I HAVE PUGS: %s', pugs)

    for p in pugs:
        outputs.append([data['channel'], p])

def _get(url, **kwargs):
    r = requests.get(url, params=kwargs)
    if r.status_code != 200:
        return {}
    return r.json()
