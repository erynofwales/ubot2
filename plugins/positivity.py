# When you just need a positive factoid for your chosen family.

import re
import random


MESSAGE_RE = re.compile(r'!positive')


# Yeah, i read some of the docs
outputs = []


# A bank that isn't a zero-sum game.
# A non-traditional bank.
# This had more complexity and thought behind it but I am drunk and do not
# remember.
POSITIVE_BANK = [
    'We can do it.',
    'We are all so wonderful.',
    'We all deserve happiness.',
    'Our family is important.',
]


def process_messsage(data):
    if 'text' not in data:
        LOGGER.error('Aw, you probably meant to give some `data` with `text` in it, try better next time.')
        return

    match = MESSAGE_RE.match(text)
    if not match:
        return

    # Almost wrote `const` because I guess I'm a JavaScript developer at heart
    statement = random.choice(POSITIVE_BANK)
    outputs.append(statement)
    # Let's write a pure function, yeah?
    # i mean lol random.choice ruins that
    # #FP2017
    return statement
