#!/usr/bin/env zsh
# Run ubot2 forever
# Eryn Wells <eryn@erynwells.me>

function start
{
    while true; do
        env/bin/python rtmbot.py
    done
}

start
