#!/usr/bin/env python3
from cloudjumper import Cloudjumper

config_name = "config.json"

with open(config_name) as config_file:
    # noinspection PyCallingNonCallable
    bot = Cloudjumper(config_file)

try:
    bot.run()
except KeyboardInterrupt:
    pass
finally:
    bot.quit(bot.messages.get("disconnect", "Gotta go save Hiccup from yet another gliding accident..."))