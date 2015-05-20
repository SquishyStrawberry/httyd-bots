#!/usr/bin/env python3

private_message = False
name_needed = True


def message_handler(bot, message, sender):
    if bot.is_command("terminate", message, name_needed):
        bot.quit()
        return True
