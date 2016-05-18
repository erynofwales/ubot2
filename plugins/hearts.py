# hearts.py
# Keepin' score is better with <3.
# Eryn Wells <eryn@erynwells.me>

import json
import os.path
import re

HEARTS_FILE = 'hearts.json'

PLUSES = {'prefix': ['++', '<3', ':heart:', '❤️'],
          'suffix': ['++']}
MINUSES = {'prefix': ['--', '–', '—', '</3', ':broken_heart:', '💔'],
           'suffix': ['--']}

outputs = []

def process_message(data):
    try:
        text = data['text']
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

    # TODO: Lots of duplicated code below. Make it better.
    operator, prefix, increment = find_operator(text)
    if operator:
        len_operator = len(operator)
        if prefix:
            name = text[len_operator:].strip()
        else:
            name = text[:-len_operator].strip()
        score = update_item(name, increment)
        outputs.append([data['channel'], '_{}_ now has a score of {}.'.format(name, score)])

def find_operator(text):
    prefix_increment = has_prefix(text, PLUSES['prefix'])
    if prefix_increment:
        return prefix_increment, True, True

    suffix_increment = has_suffix(text, PLUSES['suffix'])
    if suffix_increment:
        return suffix_increment, False, True

    prefix_decrement = has_prefix(text, MINUSES['prefix'])
    if prefix_decrement:
        return prefix_decrement, True, False

    suffix_decrement = has_suffix(text, MINUSES['suffix'])
    if suffix_decrement:
        return suffix_decrement, False, False

    return None, None, None

def top5():
    data = read_data()
    items = [(score, name) for name, score in data.items()]
    items.sort()
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
    score += 1 if increment else -1
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
