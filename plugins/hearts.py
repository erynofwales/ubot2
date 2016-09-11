# hearts.py
# Keepin' score is better with <3.
# Eryn Wells <eryn@erynwells.me>

import json
import logging
import os.path
import random
import re

HEARTS_FILE = 'hearts.json'

PLUSES = ['++', '<3', '&lt;3', ':heart:', ':yellow_heart:', ':green_heart:',  ':blue_heart:', ':purple_heart:', '❤️', '💛', '💚', '💙', '💜']
MINUSES = ['--', '–', '—', '</3', '&lt;/3', ':broken_heart:', '💔']
SASS = ['r u srs rn', 'no', 'noooope']

LOGGER = logging.getLogger('hearts')

LEADERS_RE = re.compile('!(top|bottom)(\d+)')
WHITESPACE_RE = re.compile('\s+')
LINK_RE = re.compile(r'<(?P<type>[@#])(?P<id>[A-Z0-9]+)(\|(?P<name>\w+))?>')
VAR_RE = re.compile(r'<!(?P<name>\w+)>')
EMOJI_RE = re.compile(r':\w+:')

outputs = []

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
        # Strip off the trailing : if the message is a user or group
        for regex in [LINK_RE, VAR_RE]:
            m = regex.match(text)
            if not m:
                continue
            # string is just a username with a colon at the end so strip off the colon
            if (m.end() == len(text)-1) and text.endswith(':'):
                text = text[:-1]
                break

        # If the remaining string is all emojis, ignore it
        tokenized = WHITESPACE_RE.split(text)
        emoji_matches = map(EMOJI_RE.match, tokenized)
        all_emoji = all(emoji_matches)
        if all_emoji:
            return None, None

        return score, text
    else:
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

