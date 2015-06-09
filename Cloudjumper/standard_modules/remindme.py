#!/usr/bin/env python3
import re
import time


name_needed = True
private_message = False
periods = {
    "years": 1*60*60*24*365.25,
    "months": 1*60*60*24*30,
    "weeks": 1*60*60*24*7,
    "days": 1*60*60*24,
    "hours": 1*60*60,
    "minutes": 1*60,
    "seconds": 1,
}
for key in dict(periods):
    periods[key.rstrip("s")] = periods[key]

splitter = re.compile("(?i)\s?({})\s".format("|".join(periods)))
ten_years = periods["years"] * 10

def setup_instance(inst):
    inst.irc_cursor.execute("SELECT name FROM sqlite_master WHERE TYPE=\"table\"")
    tables = inst.irc_cursor.fetchall()
    if "Reminders" not in map(lambda x: x[0], tables):
        inst.irc_cursor.execute("CREATE TABLE Reminders (id INTEGER PRIMARY KEY, user TEXT, to_remind TEXT, reply_on INTEGER, query TEXT)")


def message_handler(bot, message, sender):
    args = message.split(" ", int(name_needed)+1)
    if bot.is_command("remindme", message, name_needed):
        if len(args) >= int(name_needed)+2:
            message = args[int(name_needed)+1]
            splat = splitter.split(message, 1)
            if len(splat) != 3:
                bot.send_action(bot.get_message("command_error").format(nick=sender))
            else:
                basetime, duration, message = splat         
                duration = duration.strip().lower()
                basetime = basetime.split(" ")[-1]
                if not basetime.isdigit():
                    bot.send_action(bot.get_message("command_error").format(nick=sender))
                else:
                    realtime = int(basetime) * periods[duration]
                    if realtime > ten_years:
                        bot.send_action(bot.get_message("time_too_long"))
                        return True
                    reply_on = time.time() + realtime 
                    bot.send_action(bot.get_message("remindme_success").format(nick=sender,
                message=message, 
                reply_in=basetime, 
                reply_on=reply_on))
                    bot.irc_cursor.execute("SELECT * FROM Reminders")
                    if bot.irc_cursor.fetchone() is None:
                        bot.irc_cursor.execute("INSERT INTO Reminders VALUES (0,?,?,?,?)", 
                        (sender.lower(), 
                         message, 
                         reply_on, 
                         basetime + " " + duration))
                    else:
                        bot.irc_cursor.execute("INSERT INTO Reminders(user,to_remind,reply_on,query) VALUES (?,?,?,?)", 
                        (sender.lower(), 
                        message, 
                        reply_on, 
                        basetime + " " + duration))
        else:
            bot.send_action(bot.get_message("command_error").format(nick=sender))
        return True
    else:
        bot.irc_cursor.execute("SELECT to_remind,reply_on,query FROM Reminders WHERE user=?", (sender.lower(),))
        messages = bot.irc_cursor.fetchall()
        for msg, tm, when in messages:
            if time.time() >= tm:
                bot.send_action(bot.get_message("reminder").format(message=msg, nick=sender, time=tm, when=when))
                bot.irc_cursor.execute("DELETE FROM Reminders WHERE user=? AND to_remind=? AND reply_on=? AND query=?",
                (sender.lower(),
                 msg,
                 tm,
                 when))


    

