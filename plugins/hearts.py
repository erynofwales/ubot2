# hearts.py
# Keepin' score is better with <3.
# Eryn Wells <eryn@erynwells.me>

import json
import logging
import os.path
import re

HEARTS_FILE = 'hearts.json'

PLUSES = ['++', '<3', '&lt;3', ':heart:', ':yellow_heart:', ':green_heart:',  ':blue_heart:', ':purple_heart:', '❤️', '💛', '💚', '💙', '💜']
MINUSES = ['--', '–', '—', '</3', '&lt;/3', ':broken_heart:', '💔']

LOGGER = logging.getLogger('hearts')

outputs = []

def process_message(data):
    try:
        text = data['text'].strip()
    except KeyError:
        # TODO: Make this better.
        return

    if text == '!top5':
        scores = top5()
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

def top5():
    data = read_data()
    items = [(score, name) for name, score in data.items()]
    items.sort(key=lambda item: item[0], reverse=True)
    out = ''
    for idx in range(5):
        try:
            item = items[idx]
            out += '{}. _{}_ : {}\n'.format(idx+1, item[1], item[0])
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

