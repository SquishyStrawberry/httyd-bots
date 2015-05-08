#!/usr/bin/env python3

try:

    from thornado import Thornado

except ImportError:
    print("Couldn't Import THORNADO!")
    exit(0)

config_name = "config.json"
with open(config_name) as config_file:
    # noinspection PyCallingNonCallable
    bot = Thornado(config_file)

try:
    bot.run()
except KeyboardInterrupt:
    pass
finally:
    bot.quit(bot.messages.get("disconnect", "Gotta go feed my little Thornados."))