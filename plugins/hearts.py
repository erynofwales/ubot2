# hearts.py
# Keepin' score is better with <3.
# Eryn Wells <eryn@erynwells.me>

import json
import logging
import os.path
import random
import re

from service import slack

HEARTS_FILE = 'hearts.json'

PLUSES = ['++', '<3', '&lt;3', ':heart:', ':yellow_heart:', ':green_heart:',  ':blue_heart:', ':purple_heart:', '❤️', '💛', '💚', '💙', '💜']
MINUSES = ['--', '–', '—', '</3', '&lt;/3', ':broken_heart:', '💔']
SASS = ['r u srs rn', 'no', 'noooope']

LOGGER = logging.getLogger('hearts')

LEADERS_RE = re.compile('!(top|bottom)(\d+)')
WHITESPACE_RE = re.compile('\s+')
LINK_RE = re.compile(r'<(?P<type>[@#!])(?P<id>\w+)(\|(?P<name>\w+))?>')
EMOJI_RE = re.compile(r':\w+:')

# rtmbot interface
outputs = []

USERS = []
CHANNELS = []

#
# RTM
#

def process_hello(data):
    global USERS
    USERS = slack.users()
    CHANNELS = slack.channels()

def process_message(data):
    try:
        text = data['text'].strip()
    except KeyError:
        # TODO: Make this better.
        return

    leaders_m = LEADERS_RE.match(text)
    if leaders_m:
        top = leaders_m.group(1) == 'top'
        try:
            n = int(leaders_m.group(2))
        except ValueError:
            outputs.append([data['channel'], random.choice(SASS)])
            return
        if n == 0:
            outputs.append([data['channel'], random.choice(SASS)])
            return
        scores = leaders(n, top)
        if scores:
            outputs.append([data['channel'], scores])
        return

    if text.startswith('!erase'):
        name = text[len('!erase'):].strip()
        success = erase_score(name)
        if success:
            outputs.append([data['channel'], "Erased score for _{}_.".format(name)])
        else:
            outputs.append([data['channel'], "No score for _{}_.".format(name)])
        return

    score, name = calculate_score_and_find_operators(text)
    if score is not None and name:
        LOGGER.info('Adding %s to %s', score, name)
        if score:
            score = update_item(name, score)
            outputs.append([data['channel'], '_{}_ now has a score of {}.'.format(name, score)])
        else:
            outputs.append([data['channel'], 'No score change for _{}_.'.format(name)])

#
# Hearts
#

def calculate_score_and_find_operators(text):
    original_text = text
    score = 0

    while True:
        found = False

        op, is_prefix = has_operator(text, PLUSES)
        if op:
            text = strip_operator(text, op, is_prefix)
            score += 1
            found = True

        op, is_prefix = has_operator(text, MINUSES)
        if op:
            text = strip_operator(text, op, is_prefix)
            score -= 1
            found = True

        if not found:
            break

    did_change = original_text != text
    if did_change:
        tokenized = WHITESPACE_RE.split(text)

        # If the remaining string is all emojis, ignore it
        emoji_matches = map(EMOJI_RE.match, tokenized)
        all_emoji = all(emoji_matches)
        if all_emoji:
            LOGGER.debug('Message is all emoji, skipping')
            return None, None

        tokenized = map(strip_colon, tokenized)
        tokenized = map(swap_links_and_vars, tokenized)

        text = ' '.join(tokenized)
        LOGGER.debug('Score {} for message: {}'.format(score, text))
        return score, text
    else:
        LOGGER.debug('No score adjustment for message: {}'.format(text))
        return None, None

def strip_operator(text, operator, is_prefix):
    len_op = len(operator)
    if is_prefix:
        return text[len_op:].lstrip()
    else:
        return text[:-len_op].rstrip()

def has_operator(text, operators):
    for op in operators:
        if text.startswith(op):
            return op, True
        elif text.endswith(op):
            return op, False
    return None, None

def strip_colon(item):
    '''Remove trailing colon from messages that @ a particular user.'''
    m = LINK_RE.match(item)
    if not m:
        return item
    if not (m.end() == (len(item)-1) and item.endswith(':')):
        return item
    return item[:-1]

def swap_links_and_vars(item):
    '''
    Swap links and variables for their names. This is for things like @eryn, #general, and !everyone.
    '''
    m = LINK_RE.match(item)
    if not m:
        return item

    link_type = m.group('type')

    # Users
    if link_type == '@':
        name = m.group('name')
        if name:
            return name
        ident = m.group('id')
        users = [u for u in USERS if u['id'] == ident]
        try:
            return users[0]['name']
        except IndexError:
            return item

    # Channels
    elif link_type == '#':
        name = m.group('name')
        if name:
            return name
        ident = m.group('id')
        channels = [c for c in CHANNELS if c['id'] == ident]
        try:
            return channels[0]['name']
        except IndexError:
            return item

    # Variables (e.g. everyone, channel, here, etc)
    elif link_type == '!':
        name = m.group('name')
        return name if name else m.group('id')

    return item

def leaders(n, top=True):
    if n == 0:
        return

    data = read_data()
    items = [(score, name) for name, score in data.items()]
    items.sort(key=lambda item: item[0], reverse=top)
    out = ''

    for idx in range(n):
        try:
            item = items[idx]
            rank = idx + 1 if top else len(items) - idx
            out += '{}. _{}_ : {}\n'.format(rank, item[1], item[0])
        except IndexError:
            break

    return out

#
# Persistence
#

def erase_score(name):
    data = read_data()
    try:
        del data[name]
    except KeyError:
        return False
    else:
        write_data(data)
        return True

def read_data():
    if not os.path.exists(HEARTS_FILE):
        return {}
    with open(HEARTS_FILE) as f:
        return json.load(f)
    return None

def write_data(obj):
    with open(HEARTS_FILE, 'w') as f:
        json.dump(obj, f, sort_keys=True, indent=4)

def update_item(name, increment):
    data = read_data()
    score = data.get(name)
    if not score:
        score = 0
    score += increment
    data[name] = score
    write_data(data)
    return score

