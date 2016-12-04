# react.py
# Necessary plugin for productive Slack orgs.
# Eryn Wells <eryn@erynwells.me>

import logging
import re
import requests

LOGGER = logging.getLogger('react')

EXTENSIONS = ('', '.gif', '.png', '.jpg')
MESSAGE_RE = re.compile(r'(!react)\s+(\w+)')

#
# rtmbot interface
#

config = None
outputs = []

def process_message(data):
    if 'root' not in config:
        LOGGER.error('Please define the root URL where reactions live in config.root')
        return

    try:
        text = data['text']
    except KeyError:
        LOGGER.debug('Missing "text" key in data.')
        return

    # find the message
    match = MESSAGE_RE.match(text)
    if not match:
        return
    reaction = match.group(2)
    if not reaction:
        LOGGER.info('Reaction command but no reaction.')

    for ext in EXTENSIONS:
        url = '{}/{}{}'.format(config['root'], reaction, ext)
        LOGGER.debug('Checking url: %s', url)
        r = requests.head(url)
        if r.status_code != 200:
            continue
        outputs.append([data['channel'], url])
        break
    else:
        outputs.append([data['channel'], 'Sorry, no reaction by that name'])

