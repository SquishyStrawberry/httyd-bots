#!/usr/bin/env python3
import random

private_message = False
name_needed = True


def message_handler(bot, message, sender):
    args = message.split(" ", 2)
    if bot.is_command("attack", message, name_needed):
        if len(args) < 2+int(name_needed):
            bot.send_message(bot.get_message("command_error").format(nick=sender))
        else:
            victim = args[1+int(name_needed)]
            attacks = bot.get_message("attacks")
            if isinstance(attacks, list):
                bot.send_action(random.choice(attacks).format(target=victim))
        return True 