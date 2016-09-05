# cookie.py
# Pin management
# Eryn Wells <eryn@erynwells.me>

import logging

LOGGER = logging.getLogger('cookie')

def process_hello(data):
    # TODO: Get list of channels I'm in.
    # TODO: Query for pins from each channel.
    # TODO: Determine if a message should be unpinned to make room for next pin.
    LOGGER.info('Hello!')

def process_channel_joined(data):
    # TODO: Query for pins from this channel.
    # TODO: Determine if a message should be unpinned to make room for next pin.
    LOGGER.info('Joined #{}'.format(data['channel']['name']))

def process_pin_added(data):
    # TODO: Unpin oldest message if needed.
    # TODO: Write that pin to a file.
    LOGGER.info('Pin added')

def process_message(data):
    # TODO: !cookie
    LOGGER.info('Received message')
