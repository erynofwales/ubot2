# cowsay.py
# Necessary plugin for productive Slack orgs.
# Eryn Wells <eryn@erynwells.me>

import logging
import re
import subprocess

LOGGER = logging.getLogger('cowsay')

COWSAY_PATH = '/usr/games/cowsay'
MESSAGE_RE = re.compile(r'(!cowsay)(.*)')

outputs = []

def process_message(data):
    try:
        text = data['text']
    except KeyError:
        LOGGER.error('Missing "text" key in data.')
        return

    # find the message
    match = MESSAGE_RE.match(text)
    if not match:
        return
    cmd = match.group(1)
    if not cmd:
        return
    msg = match.group(2)
    if not msg:
        LOGGER.info('Cowsay command but no message.')

    # cowsay it up
    try:
        out = subprocess.check_output([COWSAY_PATH, msg]).decode()
    except subprocess.CalledProcessError as e:
        LOGGER.error('Error running cowsay. (%d)', e.returncode)
        return
    out = '```\n{}```'.format(out)
    outputs.append([data['channel'], out])

