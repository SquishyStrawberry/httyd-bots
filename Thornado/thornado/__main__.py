#!/usr/bin/env python3

from thornado import Thornado

config_name = "config.json"
with open(config_name) as config_file:
    # noinspection PyCallingNonCallable
    bot = Thornado(config_file)

bot.run()