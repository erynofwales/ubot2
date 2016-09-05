#!/usr/bin/env python
import sys
from argparse import ArgumentParser

import yaml
from rtmbot import RtmBot
import service


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='Full path to config file.',
        metavar='path'
    )
    return parser.parse_args()

# load args with config path
args = parse_args()
config = None
with open(args.config or 'rtmbot.conf', 'r') as f:
    config = yaml.load(f)
service.slack = service.SlackService(config.get('SLACK_TOKEN'))
bot = RtmBot(config)
try:
    bot.start()
except KeyboardInterrupt:
    sys.exit(0)
