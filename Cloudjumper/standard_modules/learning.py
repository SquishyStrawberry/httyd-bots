#!/usr/bin/env python3
import sre_constants
import re

private_message = False
name_needed = True


def message_handler(bot, message, sender):
    
    args = message.split(" ", 1+int(name_needed))
    learn_args = " ".join(args[1+int(name_needed):]).split("->", 1)
    learn_args = tuple(i.strip() for i in learn_args if i.strip())

    if bot.is_command("learn", message, name_needed):
        if len(learn_args) >= 2:
            if bot.has_flag("whitelist", sender) or bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                trigger, response = learn_args[0].strip(), learn_args[1].strip()
                # Since regex is weird, we need to escape a lone \ on the end of the line.
                
                if trigger[-1] == "\\": 
                    if len(trigger) == 1 or trigger[-2] != "\\":
                        trigger += "\\"
                try:
                    re.compile(trigger)
                except sre_constants.error:
                    bot.send_action(bot.get_message("command_error").format(nick=sender))
                    return True
                bot.send_action(bot.get_message("learn").format(nick=sender))
                bot.irc_cursor.execute("SELECT * FROM Commands WHERE trigger=?",
                                       (trigger,))
                if bot.irc_cursor.fetchone():
                    bot.send_action(bot.get_message("learn_superfluous"))
                else:
                    @bot.basic_command()
                    def dummy(*args, **kwargs):
                        return trigger, response
            else:
                bot.send_action(bot.get_message("learn_deny").format(nick=sender))
        else:
            bot.send_action(bot.get_message("learn_error").format(nick=sender))
        return True

    elif bot.is_command("forget", message, name_needed):
        trigger = learn_args[0].strip()
        if trigger[-1] == "\\": 
            if len(trigger) == 1 or trigger[-2] != "\\":
                trigger += "\\"
        if bot.has_flag("whitelist", sender) or bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
            bot.irc_cursor.execute("SELECT * FROM Commands WHERE trigger=?", (trigger,))
            response = bot.irc_cursor.fetchone()
            if response is not None:
                bot.send_action(bot.get_message("forget").format(nick=sender))
                bot.forget_basic_command(trigger)
            else:
                bot.send_action(bot.get_message("forget_superfluous"))
        else:
            bot.send_action(bot.get_message("learn_deny").format(nick=sender))      
        return True
