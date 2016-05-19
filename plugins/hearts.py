# hearts.py
# Keepin' score is better with <3.
# Eryn Wells <eryn@erynwells.me>

import json
import logging
import os.path
import re

HEARTS_FILE = 'hearts.json'

PLUSES = {'prefix': ['++', '<3', '&lt;3', ':heart:', ':yellow_heart:', ':green_heart:',  ':blue_heart:', ':purple_heart:', '❤️', '💛', '💚', '💙', '💜'],
          'suffix': ['++', '<3', '&lt;3', ':heart:', ':yellow_heart:', ':green_heart:',  ':blue_heart:', ':purple_heart:', '❤️', '💛', '💚', '💙', '💜']}
MINUSES = {'prefix': ['--', '–', '—', '</3', '&lt;/3', ':broken_heart:', '💔'],
           'suffix': ['--', '–', '—', '</3', '&lt;/3', ':broken_heart:', '💔']}

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

    LOGGER.info('Processing message: %s', text)
    score, name = calculate_score_and_find_operators(text)
    if score is not None:
        LOGGER.info('Adding %s to %s', score, name)
        if score:
            score = update_item(name, score)
            outputs.append([data['channel'], '_{}_ now has a score of {}.'.format(name, score)])
        else:
            outputs.append([data['channel'], 'No score change for _{}_.'.format(name)])

def calculate_score_and_find_operators(text):
    original_text = text
    score = 0

    times, text = _do_operators(text, PLUSES['prefix'], is_prefix=True)
    score += times

    times, text = _do_operators(text, PLUSES['suffix'], is_prefix=False)
    score += times

    times, text = _do_operators(text, MINUSES['prefix'], is_prefix=True)
    score -= times

    times, text = _do_operators(text, MINUSES['suffix'], is_prefix=False)
    score -= times

    did_change = original_text != text
    if did_change:
        return score, text
    else:
        return None, None

def _do_operators(text, operators, is_prefix):
    times = 0
    length = 0
    check_func = has_prefix if is_prefix else has_suffix
    while True:
        op = check_func(text, operators)
        if not op:
            break
        LOGGER.info('Found operator: {} (prefix = {})'.format(op, is_prefix))
        times += 1
        op_len = len(op)
        length += op_len
        if is_prefix:
            text = text[op_len:].lstrip()
        else:
            text = text[:-op_len].rstrip()
    return times, text

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

def update_item(name, increment):
    data = read_data()
    score = data.get(name)
    if not score:
        score = 0
    score += increment
    data[name] = score
    write_data(data)
    return score

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

def has_prefix(text, prefixes):
    for p in prefixes:
        if text.startswith(p):
            return p
    return None

def has_suffix(text, suffixes):
    for s in suffixes:
        if text.endswith(s):
            return s
    return None
