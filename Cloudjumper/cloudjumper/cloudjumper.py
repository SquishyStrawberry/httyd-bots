#!/usr/bin/env python3
import os
import random
import sys
import re
import requests
import json
from bs4 import BeautifulSoup

try:
    import irc_helper
except ImportError:
    for i in range(1, 6):
        parent_directory = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-i])
        if parent_directory not in sys.path:
            sys.path.insert(0, parent_directory)
        try:
            # noinspection PyUnresolvedReferences
            import irc_helper
        except ImportError:
            del sys.path[0]
        else:
            break


# From Django
url_validator = re.compile(
    r"^(?:(?:http|ftp)s?://)"  # http:// or https://
    r"((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$", re.IGNORECASE)


class CloudjumperError(irc_helper.IRCError):
    pass


# noinspection PyUnusedLocal
class Cloudjumper(irc_helper.IRCHelper):
    flags = {
        "admin": "a",
        "superadmin": "s",
        "whitelist": "w",
        "ignore": "i",
    }
    defaults = {
        "announce_arrival": "enters the arena!",
        "greetings": [
            "welcomingly nuzzles and licks {nick}",
            "welcomingly nuzzles {nick}",
            "welcomingly licks {nick}",
            "welcomingly tail-slaps {nick}",
            "playfully nuzzles and licks {nick}",
            "playfully nuzzles {nick}",
            "playfully licks {nick}",
            "playfully tail-slaps {nick}",
            "tosses a pebble at {nick}",
            "joyfully waggles his tail at {nick}'s arrival",
            "cheerfully waggles his tail at {nick}'s arrival",
            "playfully waggles his tail at {nick}'s arrival",
            "welcomes {nick} with a cheerful warble"
        ],
        "attacks": [
            "shoots a plasma bolt at {target}!",
            "hurls a pebble at {target}!",
            "tackles {target}!",
            "tail-whips {target}!",
            "charges {target}!",
            "unsheathes his teeth and bites {target}!"
        ],
        "deny": "won't follow {nick}'s instructions!",
        "disconnect": "Gotta go save Hiccup from yet another gliding accident...",
        "switch_channel": "Gotta go to fly with Hiccup...",
        "eat": "gulps down {victim}!",
        "deny_superadmin": "doesn't let non-superadmins change superadmin's flags!",
        "eat_inedible": "doesn't feel like eating {victim}!",
        "eat_superfluous": "has already eaten {victim}!",
        "forget": "forgot one of his tricks!",
        "forget_superfluous": "doesn't know that trick!",
        "ignore_me": "will no longer acknowledge your entrances.",
        "ignore_me_superfluous": "is already ignoring you.",
        "learn": "has been trained by {nick}!",
        "learn_superfluous": "already knows that trick!",
        "learn_deny": "doesn't want to be trained by {nick}!",
        "learn_error": "tilts his head in confusion towards {nick}...",
        "print_command": "{trigger} -> {response}",
        "purge_commands": "forgot all of his tricks!",
        "purge_commands_superfluous": "hasn't learned any tricks to forget!",
        "spit": "spits out {victim}!",
        "spit_superfluous": "hasn't eaten {victim} yet!",
        "stomach": "is digesting {victims}...",
        "stomach_empty": "isn't digesting anyone...",
        "urltitle": "finds the url title to be: \"\u0002{title}\"",
        "vomit": "empties his stomach!",
        "vomit_superfluous": "hasn't eaten anything yet!",
        "flag_added": "successfully added {flag} to {user}, new flags: {flags}",
        "flag_remove": "successfully removed {flag} from {user}, new flags: {flags}",
        "unexisting_flag": "knows that {nick} doesn't have that flag!",
        "unknown_flag": "doesn't know that flag!",
        "deny_command": "won't listen to you!",
        "config_closed": "can't access his config!",
        "config_reloaded": "successfully reloaded his config!"
    }

    def __init__(self, config_file):
        needed = ("user", "nick", "channel", "host", "port", "database_name", "response_delay")
        self.config_file = config_file
        self.config = json.loads(self.config_file.read())
        self.messages = self.config.get("messages", {})
        super().__init__(**{k: v for k, v in self.config.items() if k in needed})

        self.irc_cursor.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
        if "Stomach" not in map(lambda x: x[0], self.irc_cursor.fetchall()):
            self.irc_cursor.execute("CREATE TABLE Stomach (id INTEGER PRIMARY KEY, thing TEXT, real_thing TEXT)")
        self.apply_commands()
        self.add_flag("superadmin", "MysteriousMagenta")
        self.add_flag("superadmin", self.nick)

        for i in self.config.get("auto_admin", []):
            self.add_flag("superadmin", i)

        self.irc_cursor.execute("SELECT username FROM Flags WHERE flags LIKE \"%s%\"")
        for (user,) in self.irc_cursor.fetchall():
            self.add_flag("admin", user)
            self.add_flag("whitelist", user)

    def handle_block(self, block):
        block_data = super().handle_block(block)
        if block_data.get("command", "").upper() == "JOIN":
            if not self.has_flag("ignore", block_data.get("sender")):
                greeting = random.choice(self.get_message("greetings"))
                if "{nick}" in greeting:
                    greeting = greeting.format(nick=block_data.get("sender"))
                else:
                    greeting += block_data.get("sender", "")
                self.send_action(greeting)
        if block_data.get("sender") == "Toothless" and block_data.get("recipient") == self.nick:
            try:
                trigger, response = block_data.get("message", "").split("->", 1)
            except ValueError:
                # Signifies that the message is not a command.
                self.log("[Invalid Command From Toothless...]")
            else:
                self.log("[Taking Command From Toothless...]")

                @self.basic_command()
                def dummy():
                    return trigger, response
        return block_data

    def join_channel(self, channel):
        super().join_channel(channel)
        self.send_action(self.get_message("announce_arrival"))

    def add_flag(self, flag, username):
        username = username.lower()
        if flag in Cloudjumper.flags:
            flag = Cloudjumper.flags[flag]
        elif flag not in Cloudjumper.flags.values():
            raise CloudjumperError("Unknown flag! Valid flags are {}".format(", ".join(Cloudjumper.flags.values())))
        self.irc_cursor.execute("SELECT * FROM flags")
        if not self.irc_cursor.fetchone():
            self.irc_cursor.execute("INSERT INTO flags VALUES (0,?,?)", (username, flag))
        else:
            self.irc_cursor.execute("SELECT * FROM flags WHERE username=?", (username,))
            if self.irc_cursor.fetchone():
                self.irc_cursor.execute("INSERT INTO Flags(username,flags) VALUES (?,?)", (username, flag))
            else:
                old_flags = self.get_flags(username)
                new_flags = "".join(sorted(set(old_flags + tuple(flag))))
                self.irc_cursor.execute("UPDATE Flags SET flags=? WHERE username=?", (new_flags, username))

    def remove_flag(self, flag, username):
        username, flag = username.lower(), flag.lower()
        if flag in Cloudjumper.flags:
            flag = Cloudjumper.flags.get(flag)
        elif flag not in Cloudjumper.flags.values():
            raise CloudjumperError("Unknown flag! Valid flags are {}".format(", ".join(Cloudjumper.flags.values())))
        old_flags = self.get_flags(username)
        new_flags = "".join(old_flags).replace(flag, "")
        if new_flags != "":
            self.irc_cursor.execute("UPDATE Flags SET flags=? WHERE username=?", (new_flags, username))
        else:
            self.irc_cursor.execute("DELETE FROM Flags WHERE username=?", (username,))

    def get_flags(self, username):
        username = username.lower()
        self.irc_cursor.execute("SELECT flags FROM Flags WHERE username=?", (username,))
        raw_flags = self.irc_cursor.fetchone()
        if raw_flags:
            raw_flags = raw_flags[0]
        else:
            raw_flags = ""
        return tuple(raw_flags)

    def has_flag(self, flag, username):
        flag, username = flag.lower(), username.lower()
        if flag in Cloudjumper.flags:
            flag = Cloudjumper.flags[flag].lower()
        elif flag not in Cloudjumper.flags.items():
            raise CloudjumperError("Unknown flag! Valid flags are {}".format(", ".join(Cloudjumper.flags.values())))
        flags = self.get_flags(username)
        return flag in flags

    def get_message(self, message_key):
        return self.messages.get(message_key, Cloudjumper.defaults.get(message_key))

    def apply_commands(self):
        """
        A base set of commands.
        Arguments:
            bot: A IRCHelper instance.
        Effect:
            Adds a bunch of sample commands to bot.
        """

        @self.advanced_command(False)
        def url_title(bot: Cloudjumper, message: str, sender: str):
            url_match = url_validator.search(message.strip())
            if not url_match:
                return
            req = requests.get(message.strip(), headers={"User-Agent": "Py3 TitleFinder"})
            if req.ok:
                soup = BeautifulSoup(req.text)
                bot.send_action(self.get_message("urltitle").format(
                    title=soup.title.text))
                # TODO Implement proper Youtube API
            else:
                bot.send_action("wasn't able to get URL info! [{}]".format(sender, req.status_code))
            return True

        @self.advanced_command(False)
        def learn_trigger(bot: Cloudjumper, message: str, sender: str):
            command = " ".join(message.split(" ")[:2]).lower()
            respond_to = (bot.nick.lower() + "! learn").lower()
            if command == respond_to and len(message.split("->", 1)) >= 2:
                if bot.has_flag("whitelist", sender) or bot.has_flag("admin", sender) or bot.has_flag("superadmin",
                                                                                                      sender):
                    trigger, response = message.split(" ", 2)[2].split("->", 1)
                    trigger, response = trigger.strip(), response.strip()
                    bot.irc_cursor.execute("SELECT * FROM Commands WHERE trigger=? AND response=?",
                                           (trigger, response))
                    if not bot.irc_cursor.fetchone():
                        bot.send_action(self.get_message("learn").format(nick=sender))

                        @self.basic_command()
                        def learn_comm():
                            return trigger, response
                    else:
                        bot.send_action(self.get_message("learn_superfluous"))
                elif not bot.has_flag("whitelist", sender):
                    bot.send_action(
                        self.get_message("learn_deny").format(nick=sender))
                else:
                    bot.send_action(
                        self.get_message("learn_error").format(
                            nick=sender))
                return True

        @self.advanced_command(False)
        def forget_trigger(bot: Cloudjumper, message: str, sender: str):
            command = " ".join(message.split(" ")[:2]).lower()
            respond_to = (bot.nick.lower() + "! forget").lower()
            if command == respond_to and len(message.split(" ")) >= 3:
                if bot.has_flag("whitelist", sender) or bot.has_flag("admin", sender) or bot.has_flag("superadmin",
                                                                                                      sender):
                    trigger = message.split(" ", 2)[2]
                    bot.irc_cursor.execute("SELECT response FROM Commands WHERE trigger=?", (trigger,))
                    response = (bot.irc_cursor.fetchone() or [None])[0]
                    if response is not None:
                        bot.send_action(self.get_message("forget").format(nick=sender))
                        bot.forget_basic_command(trigger)
                    else:
                        bot.send_action(self.get_message("forget_superfluous").format(nick=sender))
                else:
                    bot.send_action("doesn't want to be trained by {nick}!".format(nick=sender))
                return True

        @self.advanced_command(False)
        def attack(bot: Cloudjumper, message: str, sender: str):
            command = " ".join(message.split(" ")[:2]).lower()
            respond_to = (bot.nick.lower() + "! attack").lower()
            if command == respond_to and len(message.split(" ")) >= 3:
                chosen_attack = random.choice(bot.get_message("attacks"))
                victim = message.split(" ", 2)[2]
                if "{target}" in chosen_attack:
                    chosen_attack = chosen_attack.format(target=victim)
                else:
                    chosen_attack += victim
                bot.send_action(chosen_attack)
                return True

        @self.advanced_command(False)
        def eat(bot: Cloudjumper, message: str, sender: str):
            command = " ".join(message.split(" ")[:2]).lower()
            respond_to = (bot.nick.lower() + "! eat").lower()
            if command == respond_to and len(message.split(" ")) >= 3:
                victim = message.split(" ", 2)[2]
                if victim.lower() not in map(lambda x: x.lower(), bot.config.get("inedible_victims", [])):
                    self.irc_cursor.execute("SELECT thing FROM Stomach")
                    stomach = self.irc_cursor.fetchall()
                    if victim not in stomach:
                        bot.send_action(self.get_message("eat").format(victim=victim))
                        bot.irc_cursor.execute("SELECT * FROM Stomach")
                        if not bot.irc_cursor.fetchone():
                            bot.irc_cursor.execute("INSERT INTO Stomach VALUES (0,?,?)", (victim.lower(),victim))
                        else:
                            bot.irc_cursor.execute("INSERT INTO Stomach(thing,real_thing) VALUES (?,?)", (victim.lower(),victim))
                    else:
                        bot.send_action(bot.get_message("eat_superfluous"))
                else:
                    bot.send_action(self.get_message("eat_inedible").format(victim=victim))
                return True

        @self.advanced_command(False)
        def spit(bot: Cloudjumper, message: str, sender: str):
            command = " ".join(message.split(" ")[:2]).lower()
            respond_to = (bot.nick.lower() + "! spit").lower()
            if command == respond_to and len(message.split(" ")) >= 3:
                victim = message.split(" ", 2)[2]
                bot.irc_cursor.execute("SELECT * FROM Stomach WHERE thing=?", (victim.lower(),))
                if bot.irc_cursor.fetchone():
                    # noinspection PyUnresolvedReferences
                    bot.irc_cursor.execute("DELETE FROM Stomach WHERE thing=?", (victim.lower(),))
                    bot.send_action("spits out {}!".format(victim))
                else:
                    bot.send_action("hasn't eaten {} yet!".format(victim))
            return command == respond_to and len(message.split(" ")) >= 3

        @self.advanced_command(False)
        def show_stomach(bot: Cloudjumper, message: str, sender: str):
            command = " ".join(message.split(" ")[:2]).lower()
            respond_to = (bot.nick.lower() + "! stomach").lower()
            if command == respond_to:
                self.irc_cursor.execute("SELECT real_thing FROM Stomach")
                stomach = self.irc_cursor.fetchall()
                if stomach:
                    stomachs = ", ".join(map(lambda x: x[0], stomach))
                    bot.send_action(bot.get_message("stomach").format(victims=stomachs))
                else:
                    bot.send_action(bot.get_message("stomach_empty"))
                return True

        @self.advanced_command(False)
        def vomit(bot: Cloudjumper, message: str, sender: str):
            command = " ".join(message.split(" ")[:2]).lower()
            respond_to = (bot.nick.lower() + "! vomit").lower()
            if command == respond_to:
                bot.irc_cursor.execute("SELECT * FROM Stomach")
                if bot.irc_cursor.fetchone():
                    bot.send_action(self.get_message("vomit"))
                    bot.irc_cursor.execute("DELETE FROM Stomach")
                else:
                    bot.send_action(self.get_message("vomit_superfluous"))
                return True

        @self.advanced_command(True)
        def clear_commands(bot: Cloudjumper, message: str, sender: str):
            if message.lower().split(" ")[0] == "purge_commands":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    bot.irc_cursor.execute("SELECT * FROM Commands")
                    if not bot.irc_cursor.fetchall():
                        bot.send_action(self.get_message("purge_commands_superfluous"), sender)
                    else:
                        bot.irc_cursor.execute("DELETE FROM Commands")
                        bot.send_action(self.get_message("purge_commands"), sender)

                else:
                    bot.send_action(bot.get_message("deny_command"), sender)
                return True

        @self.advanced_command(True)
        def terminate(bot: Cloudjumper, message: str, sender: str):
            if message.split(" ")[0] == "terminate":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    bot.log("[Terminating...]")
                    bot.quit(bot.get_message("disconnect"))
                else:
                    bot.send_action(bot.get_message("deny_command"), sender)

        @self.advanced_command(True)
        def list_commands(bot: Cloudjumper, message: str, sender: str):
            if message.lower().split(" ")[0] == "list_commands":
                bot.irc_cursor.execute("SELECT trigger,response FROM Commands")
                for trigger, response in bot.irc_cursor.fetchall():
                    bot.send_message(
                        self.get_message("print_command").format(trigger=trigger,
                                                                 response=response),
                        sender)
                return True

        @self.advanced_command(True)
        def copy_original(bot: Cloudjumper, message: str, sender: str):
            if message == "copy_original":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    bot.copying = True
                    bot.send_action(self.get_message("copy_original"), sender)
                    bot.send_message("list_commands", "Toothless")

                else:
                    bot.send_action(bot.get_message("deny_command"), sender)
                return True

        @self.advanced_command(True)
        def add_flag_pm(bot: Cloudjumper, message: str, sender: str):
            if message.split(" ")[0] == "add_flag":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    user, flag = map(lambda x: x.lower(), message.split(" ")[1:3])
                    try:
                        if not bot.has_flag("superadmin", sender) and bot.has_flag("superadmin", user):
                            bot.send_action(
                                bot.get_message("deny_superadmin"),
                                sender)
                        else:
                            bot.add_flag(flag, user)

                    except CloudjumperError:
                        bot.send_action(bot.get_message("unknown_flag"), sender)
                    else:
                        flags = "".join(bot.get_flags(user)) or "None"
                        bot.send_action(bot.get_message("flag_added").
                                        format(user=user, flag=flag, flags=flags), sender)
                else:
                    bot.send_action(bot.get_message("deny_command"), sender)
                return True

        @self.advanced_command(True)
        def rm_flag_pm(bot: Cloudjumper, message: str, sender: str):
            if message.split(" ")[0] == "remove_flag":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    user, flag = map(lambda x: x.lower(), message.split(" ")[1:3])

                    if flag not in bot.get_flags(user):
                        bot.send_action(bot.get_message("unexisting_flag").format(nick=user))
                        return
                    try:
                        if not bot.has_flag("superadmin", sender) and bot.has_flag("superadmin", user):
                            bot.send_action(
                                bot.get_message("deny_superadmin"),
                                sender)
                        else:
                            bot.remove_flag(flag, user)

                    except CloudjumperError:
                        bot.send_action(bot.get_message("unknown_flag"), sender)
                    else:
                        flags = "".join(bot.get_flags(user)) or "None"
                        bot.send_action(bot.get_message("flag_removed").
                                        format(user=user, flag=flag, flags=flags), sender)
                else:
                    bot.send_action(bot.get_message("deny_command"), sender)
                return True

        @self.advanced_command(True)
        def reload_config(bot: Cloudjumper, message: str, sender: str):
            if message.split(" ")[0].lower() == "reload_config":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    if not bot.config_file.closed:
                        bot.config_file.close()
                    bot.config_file = open(bot.config_file.name, bot.config_file.mode)
                    bot.config = json.loads(bot.config_file.read())
                    bot.messages = bot.config.get("messages", {})
                    bot.send_action(bot.get_message("config_reloaded"), sender)

                else:
                    bot.send_action(bot.get_message("deny_command"), sender)
                return True

        @self.advanced_command(True)
        def move_channel(bot: Cloudjumper, message: str, sender: str):
            if message.split(" ")[0].lower() == "move_channel":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    channel = message.split(" ")[1].lower()
                    bot.leave_channel(bot.get_message("switch_channel"))
                    bot.join_channel(channel)

                else:
                    bot.send_action(bot.get_message("deny_command"), sender)
                return True

        @self.advanced_command(True)
        def move_channel(bot: Cloudjumper, message: str, sender: str):
            if message.split(" ")[0].lower() == "move_channel":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    channel = message.split(" ")[1].lower()
                    bot.leave_channel(bot.get_message("switch_channel"))
                    bot.join_channel(channel)

                else:
                    bot.send_action(bot.get_message("deny_command"), sender)
                return True

        @self.advanced_command(True)
        def move_channel(bot: Cloudjumper, message: str, sender: str):
            if message.split(" ")[0].lower() == "move_channel":
                if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                    channel = message.split(" ")[1].lower()
                    bot.leave_channel(bot.get_message("switch_channel"))
                    bot.join_channel(channel)

                else:
                    bot.send_action(bot.get_message("deny_command"), sender)
                return True

        @self.advanced_command(True)
        def ignore_me(bot: Cloudjumper, message: str, sender: str):
            if message.split(" ")[0].lower() == "ignore_me":
                if not bot.has_flag("ignore", sender):
                    bot.add_flag("ignore", sender)
                    bot.send_action(bot.get_message("ignore"), sender)
                else:
                    bot.send_action(bot.get_message("ignore_superfluous"), sender)
