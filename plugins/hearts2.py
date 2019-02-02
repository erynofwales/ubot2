#!/usr/bin/env python3
# Eryn Wells <eryn@erynwells.me>

import json
import logging
import os
import re
from service import slack

HEARTS_FILE = 'hearts.json'
LOG = logging.getLogger('hearts2')

USERS = []
CHANNELS = []

#
# RTM
#

# rtmbot interface
outputs = []

LEADERS_RE = re.compile('!(top|bottom)(\d+)')
SASS = ['r u srs rn', 'no', 'noooope']

def process_hello(data):
    global USERS, CHANNELS
    USERS = slack.users()
    CHANNELS = slack.channels()

def process_message(data):
    try:
        text = data['text']
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

    score_pair = parse(text)
    if score_pair is not None:
        name = score_pair[0]
        score = score_pair[1]
        LOG.info('Adding %s to %s', score, name)
        if score != 0:
            score = update_item(name, score)
            outputs.append([data['channel'], '_{}_ now has a score of {}.'.format(name, score)])
        else:
            outputs.append([data['channel'], 'No score change for _{}_.'.format(name)])

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
# GRAMMAR
#

tokens = ('POP', 'DPOP', 'NOP', 'NAME', 'WORD', 'STR')

def t_POP(t):
    r'\+\+|:((yellow|green|blue|purple)_)?heart:|<3|&lt;3'
    LOG.debug('t_POP {}'.format(t.value))
    t.value = 1
    return t

def t_DPOP(t):
    r':(two|revolving)_hearts:'
    LOG.debug('t_DPOP {}'.format(t.value))
    t.value = 2
    return t

def t_NOP(t):
    r'--|</3|:broken_heart:'
    LOG.debug('t_NOP {}'.format(t.value))
    t.value = -1
    return t

def t_NAME(t):
    r'<(?P<type>[@#!])(?P<id>\w+)(\|(?P<name>\w+))?>:?'
    LOG.debug('t_NAME {}'.format(t.value))
    m = t.lexer.lexmatch
    typ = m.group('type')
    idee = m.group('id')
    name = m.group('name')
    if typ == '@':
        # It's a person!
        if name:
            t.value = name
        elif idee:
            users = [u for u in USERS if u['id'] == idee]
            try:
                t.value = users[0]['name']
            except IndexError:
                t.value = idee
        return t
    elif typ == '#':
        # It's a channel!
        if name:
            t.value = name
        elif idee:
            channels = [c for c in CHANNELS if c['id'] == idee]
            try:
                t.value = channels[0]['name']
            except IndexError:
                t.value = idee
        return t
    elif typ == '!':
        # It's a variable!
        t.value = name if name else idee
        return t
    else:
        return None

def t_STR(t):
    r'"[^"]*"|' r"'[^']*'|" r'“[^“”]*”|' r'‘[^‘’]*’'
    LOG.debug('t_STR {}'.format(t.value))
    t.value = t.value[1:-1]
    return t

def t_WORD(t):
    r'\w+'
    LOG.debug('t_WORD {}'.format(t.value))
    t.value = t.value.replace('_', ' ')
    return t

t_ignore = ' \t'

def t_error(t):
    out = "Lexer error: '{}'".format(t.value[0])
    LOG.debug(out)
    raise InputError(out)

import ply.lex as lex
lexer = lex.lex()

def p_line_infix(p):
    'line : oplist item oplist'
    value = p[1] + p[3]
    p[0] = (p[2], value)

def p_line_suffix(p):
    'line : item oplist'
    p[0] = (p[1], p[2])

def p_line_prefix(p):
    'line : oplist item'
    p[0] = (p[2], p[1])

def p_oplist_continue(p):
    'oplist : op oplist'
    p[0] = p[1] + p[2]
    LOG.debug('oplist: {} = {} {}'.format(p[0], p[1], p[2]))

def p_oplist_single(p):
    'oplist : op'
    p[0] = p[1]
    LOG.debug('oplist: {}'.format(p[1]))

def p_op(p):
    '''op : POP
          | DPOP
          | NOP'''
    p[0] = p[1]
    LOG.debug('op: {}'.format(p[1]))

def p_item(p):
    '''item : NAME
            | WORD
            | STR'''
    p[0] = p[1]
    LOG.debug('item: name = "{}"'.format(p[1]))

def p_error(p):
    out = "Syntax error: '{}'".format(p.value if p else p)
    LOG.debug(out)
    raise InputError(out)

import ply.yacc as yacc
parser = yacc.yacc()

class InputError(ValueError):
    pass

def parse(inp):
    try:
        return parser.parse(inp)
    except InputError:
        return None

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

#
# TESTING
#

import unittest

class TestHearts(unittest.TestCase):
    def test_words_without_ops(self):
        self.check_result_none('abc')

    def test_words_with_underscores(self):
        self.check_result('abc_def++', 'abc def', 1)

    def test_words_with_ops(self):
        self.check_result('abc++', 'abc', 1)
        self.check_result('abc--', 'abc', -1)
        self.check_result('++abc', 'abc', 1)
        self.check_result('--abc', 'abc', -1)
        self.check_result('++abc++', 'abc', 2)
        self.check_result('--abc--', 'abc', -2)

    def test_words_with_stacked_ops(self):
        self.check_result('abc++++', 'abc', 2)
        self.check_result('abc--++', 'abc', 0)

    def test_quoted_strings(self):
        self.check_result('"the quick brown fox"++', 'the quick brown fox', 1)
        self.check_result("'the quick brown fox' ++", 'the quick brown fox', 1)
        self.check_result("++'the quick brown fox'", 'the quick brown fox', 1)
        self.check_result("++ 'the quick brown fox'", 'the quick brown fox', 1)

    def test_pops(self):
        self.check_result('abc :heart:', 'abc', 1)
        self.check_result('abc :green_heart:', 'abc', 1)
        self.check_result('abc :blue_heart:', 'abc', 1)
        self.check_result('abc :purple_heart:', 'abc', 1)
        self.check_result('abc :yellow_heart:', 'abc', 1)
        self.check_result('<3 abc', 'abc', 1)

    def test_double_pops(self):
        self.check_result('abc :two_hearts:', 'abc', 2)
        self.check_result('abc :revolving_hearts:', 'abc', 2)

    def test_nops(self):
        self.check_result('-- abc', 'abc', -1)
        self.check_result(':broken_heart: abc', 'abc', -1)
        self.check_result('</3 abc', 'abc', -1)

    def test_names(self):
        self.check_result('++ <@uid>', 'uid', 1)
        self.check_result('++ <@uid|eryn>', 'eryn', 1)
        self.check_result('++ <#uid|general>', 'general', 1)
        self.check_result('++ <#uid>', 'uid', 1)
        self.check_result('-- <!e|everyone>', 'everyone', -1)
        # Colons should be stripped
        self.check_result('<@eryn>:++', 'eryn', 1)
        self.check_result('<@eryn>: ++', 'eryn', 1)

    def test_whole_lines_only(self):
        self.check_result_none('++abc def')
        self.check_result_none('abc++ def')
        self.check_result_none('ghi abc++ def')
        self.check_result_none('ghi abc def++')

    def check_result(self, inp, name, value):
        with self.subTest(input=inp):
            r = parse(inp)
            self.assertEqual(r[0], name)
            self.assertEqual(r[1], value)

    def check_result_none(self, inp):
        with self.subTest(input=inp):
            r = parse(inp)
            self.assertIsNone(r)

#
# MAIN
#

import sys

def main():
    #rootlog = logging.getLogger('')
    #rootlog.addHandler(logging.StreamHandler())
    #rootlog.setLevel(logging.DEBUG)
    unittest.main(verbosity=2, buffer=True)

if __name__ == '__main__':
    main()
