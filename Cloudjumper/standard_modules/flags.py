#!/usr/bin/env python3

private_message = True
name_needed = False

def message_handler(bot, message, sender):
    args = message.split(" ")

    if not len(args)-(int(name_needed)+1):
        return

    user = args[1].lower()
    if len(args) >= 3:
        flag = args[2]
    else:
        flag = None

    if flag in getattr(bot.__class__, "flags", []):
        flag = bot.__class__.flags[flag]
    user_flags = bot.get_flags(user)

    if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
        if flag is not None:
            if bot.is_command("add_flag", message, name_needed):
                if flag not in user_flags:
                    bot.add_flag(flag, user)
                    new_flags = ", ".join(bot.get_flags(user))
                    bot.send_action(bot.get_message("flag_added").format(user=user, flag=flag, flags=new_flags), sender)
                else:
                    bot.send_action(bot.get_message("flag_add_superfluous").format(user=user), sender)  
            elif bot.is_command("remove_flag", message, name_needed):
                if flag not in user_flags:
                    bot.send_action(bot.get_message("flag_remove_superfluous").format(user=user), sender)
                else:
                    bot.remove_flag(flag, user)
                    new_flags = ", ".join(bot.get_flags(user))
                    bot.send_action(bot.get_message("flag_remove").format(flag=flag, flags=new_flags, user=user), sender)
            
        elif bot.is_command("list_flags", message, name_needed):
            if user_flags:
                bot.send_action(bot.get_message("list_flags").format(user=user, flags=", ".join(user_flags)), sender)
            else:
                bot.send_action(bot.get_message("list_flags_error").format(user=user, flags=", ".join(user_flags)), sender)

        return True
