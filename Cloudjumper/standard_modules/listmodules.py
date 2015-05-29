#!/usr/bin/env python3

private_message = False
name_needed = True

def message_handler(bot, message, sender):
    if bot.is_command("modules", message, name_needed):
        modules = ", ".join(i.__name__ for i in tuple(bot.channel_commands) + tuple(bot.private_commands))
        bot.send_action(bot.get_message("list_modules").format(modules=modules))
        return True
