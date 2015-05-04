#!/usr/bin/env python3
from cloudjumper import Cloudjumper

config_name = "config.json"

with open(config_name) as config_file:
    # noinspection PyCallingNonCallable
    bot = Cloudjumper(config_file)

bot.run()