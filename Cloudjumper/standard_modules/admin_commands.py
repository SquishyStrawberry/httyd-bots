#!/usr/bin/env python3

private_message = True
name_needed = False


def message_handler(bot, message, sender):
    args = message.split(" ")
    if bot.has_flag("admin", sender):
        if bot.is_command("purge_commands", message, name_needed):
            bot.irc_cursor.execute("SELECT * FROM Commands")
            if bot.irc_cursor.fetchone() is not None:
                bot.irc_cursor.execute("DELETE FROM Commands")
                bot.send_action(bot.get_message("purge_commands"), sender)
            else:
                bot.send_action(bot.get_message("purge_commands_superfluous"), sender)
            return True

        elif bot.is_command("list_commands", message, name_needed):
            bot.irc_cursor.execute("SELECT trigger,response FROM Commands")
            commands = bot.irc_cursor.fetchall()
            if commands:
                for trigger, response in commands:
                    bot.send_action(bot.get_message("print_command").format(trigger=trigger, 
                                                                            response=response), sender)
            else:
                bot.send_action(bot.get_message("no_commands"), sender)
            return True
        
        elif bot.is_command("move_channel", message, name_needed):
            if len(args) < int(name_needed)+2:
                bot.send_action(bot.get_message("command_error").format(nick=sender), sender)
            else:
                bot.leave_channel(bot.get_message("switch_channel"))
                bot.join_channel(args[int(name_needed)+2])
            return True

        elif bot.is_command("reload_config", message, name_needed):
            if not bot.config_file.closed:
                bot.config_file.close()
        
            bot.config_file = open(bot.config_file.name, bot.config_file.mode)
            bot.config = json.load(bot.config_file)
            bot.messages = bot.config.get("messages", {})
        
            bot.send_action(bot.get_message("config_reloaded"), sender)
            default_path = os.path.abspath(__file__).split(os.sep)[:-1] + os.sep + "defaults.json"
            with open(os.sep.join(default_path)) as default_file:
                bot.__class__.defaults = json.loads(default_file.read())
        
            return True
