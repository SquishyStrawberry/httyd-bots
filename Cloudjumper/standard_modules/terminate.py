#!/usr/bin/env python3

private_message = False
name_needed = True


def message_handler(bot, message, sender):
    if bot.is_command("terminate", message, name_needed):
        if bot.has_flag("admin", user):
            bot.quit()
        return True
    elif bot.is_command("crash", message, name_needed):
        if bot.has_flag("admin", user):
            bot.quit()
            raise SyntaxError("Invalid Syntax: Apple Should Be In Tree.")
        return True
