# countdown.py
# Count down from the specified number
# Eryn Wells <eryn@erynwells.me>

import logging
import re

LOGGER = logging.getLogger('countdown')
MESSAGE_RE = re.compile(r'(!countdown)\s+(\d+)')

# rtmbot interface
crontable = []
outputs = []

# Check countdowns every second.
crontable.append([1, "_do_countdown"])

# countdowns in flight.
COUNTDOWNS = []

def process_message(data):
    try:
        text = data['text']
    except KeyError:
        LOGGER.error('Missing "text" key in data.')
        return

    match = MESSAGE_RE.match(text)
    if not match:
        return
    cmd = match.group(1)
    if not cmd:
        return
    try:
        n = int(match.group(2))
    except ValueError:
        LOGGER.error('Expected number but got {}'.format(match.group(2)))
        return

    _setup_timer(data['channel'], n)

def _setup_timer(channel, time):
    COUNTDOWNS.append([channel, time])

def _do_countdown():
    global COUNTDOWNS

    if len(COUNTDOWNS) == 0:
        return

    LOGGER.debug('Processing countdowns: {}'.format(COUNTDOWNS))

    for count in COUNTDOWNS:
        out = str(count[1]) if count[1] > 0 else "go"
        count[1] -= 1
        outputs.append([count[0], out])

    # Remove expired timers.
    COUNTDOWNS = list(filter(lambda c: c[1] >= 0, COUNTDOWNS))
