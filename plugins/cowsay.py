# cowsay.py
# Necessary plugin for productive Slack orgs.
# Eryn Wells <eryn@erynwells.me>

import logging
import re
import subprocess

LOGGER = logging.getLogger('cowsay')

MESSAGE_RE = re.compile(r'(!cowsay)(.*)')

#
# rtmbot interface
#

config = None
outputs = []

def process_message(data):
    if 'path' not in config:
        LOGGER.error('Please define config.path pointing to the cowsay binary.')
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
    cmd = match.group(1)
    if not cmd:
        return
    msg = match.group(2)
    if not msg:
        LOGGER.info('Cowsay command but no message.')

    # cowsay it up
    try:
        out = subprocess.check_output([config['path'], msg]).decode()
    except subprocess.CalledProcessError as e:
        LOGGER.error('Error running cowsay. (%d)', e.returncode)
        return
    out = '```\n{}```'.format(out)
    outputs.append([data['channel'], out])

