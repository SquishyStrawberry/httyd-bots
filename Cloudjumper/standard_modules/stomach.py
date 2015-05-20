#!/usr/bin/env python3

private_message = False
name_needed = True


def setup_instance(inst):
    inst.irc_cursor.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
    tables = map(lambda x: x[0], inst.irc_cursor.fetchall() or [])
    if "Stomach" not in tables:
        inst.irc_cursor.execute("CREATE TABLE Stomach (id INTEGER PRIMARY KEY, thing TEXT, real_thing TEXT)")


def message_handler(bot, message, sender):

    args = message.split(" ", 2)
    # Common Victim.
    if len(args) >= 2 + int(name_needed):
        victim = args[1 + int(name_needed)]
    else:
        victim = None

    if bot.is_command("stomach", message, name_needed):
        bot.irc_cursor.execute("SELECT real_thing FROM Stomach")
        stomach = bot.irc_cursor.fetchall()
        if stomach:
            stomachs = ", ".join(map(lambda x: x[0], stomach))
            bot.send_action(bot.get_message("stomach").format(victims=stomachs))
        else:
            bot.send_action(bot.get_message("stomach_empty"))
        return True

    elif bot.is_command("vomit", message, name_needed):
        bot.irc_cursor.execute("SELECT * FROM Stomach")
        if bot.irc_cursor.fetchone():
            bot.send_action(bot.get_message("vomit"))
            bot.irc_cursor.execute("DELETE FROM Stomach")
        else:
            bot.send_action(bot.get_message("vomit_superfluous"))
        return True


    elif bot.is_command("spit", message, name_needed):
        if victim is not None:
            bot.irc_cursor.execute("SELECT * FROM Stomach WHERE thing=?",
                                   (victim.lower(),))
            if bot.irc_cursor.fetchone():
                bot.irc_cursor.execute("DELETE FROM Stomach WHERE thing=?",
                                       (victim.lower(),))
                bot.send_action(bot.get_message("spit").format(victim=victim))
            else:
                bot.send_action(bot.get_message("spit_superfluous").format(victim=victim))
        else:
            bot.send_action(bot.get_message("command_error").format(nick=sender))
        return True

    elif bot.is_command("eat", message, name_needed):
        if victim is not None:
            inedible = map(lambda x: x.lower(),
                           bot.config.get("inedible_victims", []))
            if victim.lower() not in inedible:
                bot.irc_cursor.execute("SELECT thing FROM Stomach")
                stomach = map(lambda x: x[0], bot.irc_cursor.fetchall() or [])
                if victim not in stomach:
                    bot.send_action(bot.get_message("eat").format(victim=victim))
                    bot.irc_cursor.execute("SELECT * FROM Stomach")
                    if not bot.irc_cursor.fetchone():
                        bot.irc_cursor.execute("INSERT INTO Stomach VALUES (0,?,?)",
                                               (victim.lower(), victim))
                    else:
                        bot.irc_cursor.execute("INSERT INTO Stomach(thing,real_thing) VALUES (?,?)",
                                               (victim.lower(), victim))
                else:
                    bot.send_action(bot.get_message("eat_superfluous"))
            else:
                bot.send_action(bot.get_message("eat_inedible").format(victim=victim))
        else:
            bot.send_action(bot.get_message("command_error").format(nick=sender))
        return True
