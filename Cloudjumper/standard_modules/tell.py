#!/usr/bin/env python3

private_message = False
name_needed = True

def setup_instance(inst):
    inst.irc_cursor.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
    tables = tuple(map(lambda x: x[0], inst.irc_cursor.fetchall()))
    if "Whispers" not in tables:
        inst.irc_cursor.execute("CREATE TABLE Whispers (id INTEGER PRIMARY KEY, user TEXT, message TEXT, sender TEXT)")
    

def message_handling(bot, message, sender):
    args = message.split(" ", 3)
    
    if bot.is_command("tell", message, name_needed):
        if len(args) < int(name_needed) + 3:
            bot.send_message(bot.get_message("command_error").format(nick=sender))
        else:
            user, whisper = args[2:]
            user = user.lower()
            if user == sender.lower(): 
                bot.send_action(bot.get_message("mail_self"))
            elif user == bot.nick.lower():
                bot.send_action(bot.get_message("mail_bot"))
            else:
                bot.send_action(bot.get_message("mail_okay"))
                bot.irc_cursor.execute("SELECT * FROM Whispers")
                whispers = bot.irc_cursor.fetchall()
                if whispers:
                    bot.irc_cursor.execute("INSERT INTO Whispers(user,message,sender) VALUES (?,?,?)",
                                           (user, whisper, sender))
                else:
                    bot.irc_cursor.execute("INSERT INTO Whispers VALUES (0,?,?,?)",
                                           (user, whisper, sender))
            return True