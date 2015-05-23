#!/usr/bin/env python3

private_message = False
name_needed = True

def message_handler(bot, message, sender):
    if bot.is_command("blokes", message, name_needed):
        if bot.config.get("blokes_url"):
            bot.send_action(bot.get_message("blokes_board").format(bot.config.get("blokes_url")))
        else:
            bot.send_action(bot.get_message("blokes_board_fail"))
        return True
    elif bot.is_command("location", message, name_needed):
        if bot.config.get("github_location"):
            bot.send_action(bot.get_message("location").format(bot.config.get("github_location")))
        else:
            bot.send_action(bot.get_message("location_fail"))
        return True
    elif bot.is_command("version", message, name_needed):
        bot.send_action(bot.get_message("version").format(version=getattr(bot.__class__, "version", 1337)))
        return True
