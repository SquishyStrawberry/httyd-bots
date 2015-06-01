#!/usr/bin/env python3
import logging
import os
import random
import re
import glob
import requests
import json
import irc_helper
import importlib
from bs4 import BeautifulSoup


class CloudjumperError(irc_helper.IRCError):
    pass


class Cloudjumper(irc_helper.IRCHelper):
    flags = {
        "admin": "a",
        "superadmin": "s",
        "whitelist": "w",
        "ignore": "i",
    }
    defaults = None
    config_name = "config.json"
    # Hard coded on purpose.
    excluded_nicknames = ("skullcrusher", "thornado")
    plugins = []
    cloudjumper_logger = logging.getLogger(__name__)
    version = 2.005


    def __init__(self, config_file, extra_settings={}):
        super_args = \
            ("user", "nick", "channel",
             "host", "port", "database_name",
             "response_delay", "fail_after", "check_login",
             "use_ssl", "print_commands")

        self.config_file = config_file
        self.config = json.load(self.config_file)
        self.config.update(extra_settings)
        self.messages = self.config.get("messages", {})
        self.set_level()

        super().__init__(**{k: v for k, v in self.config.items() if k in super_args})

        self.config["inedible_victims"] = set(self.config.get("inedible_victims", []))
        self.config["inedible_victims"].add(self.nick)
        
        self.irc_cursor.execute("SELECT username FROM Flags WHERE flags LIKE \"%s%\"")
        for (user,) in self.irc_cursor.fetchall():
            self.add_flag("admin", user)
            self.add_flag("whitelist", user)

        for setting in self.config.get("auto_admin", []):
            self.add_flag("superadmin", setting)

        if self.config.get("plugins") is not None:
            Cloudjumper.plugins.append(self.config["plugins"]) 

        # Make sure this is the last line in __init__!
        self.apply_commands()           


    def extra_handling(self, block_data):
        if block_data.get("sender", "").lower() in Cloudjumper.excluded_nicknames:
            return block_data
        block_data = super().extra_handling(block_data)
        if block_data.get("command", "").upper() == "JOIN":
            if not self.has_flag("ignore", block_data.get("sender")):
                greeting = random.choice(self.get_message("greetings")).format(
                    nick=block_data.get("sender"))
                self.send_action(greeting)

        if self.since_last_comment(block_data.get("sender", "")) < self.response_delay:
            return block_data

        if block_data.get("recipient") == self.channel and block_data.get("sender"):

            self.irc_cursor.execute("SELECT message,sender FROM Whispers WHERE user=?",
                                    (block_data.get("sender").lower(),))
            messages = self.irc_cursor.fetchall()
            if messages:
                self.send_action(self.get_message("announce_mail").format(nick=block_data.get("sender")))
                for message, sender in messages:
                    self.send_action(self.get_message("send_mail").format(message=message, sender=sender),
                                     block_data.get("sender"))
            self.irc_cursor.execute("DELETE FROM Whispers WHERE user=?", (block_data.get("sender").lower(),))
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
            if not self.irc_cursor.fetchone():
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
        if new_flags:
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
        return self.messages.get(message_key, Cloudjumper.defaults.get(message_key, "couldn't find a valid message"))

    def start_up(self):
        super().start_up()
        if self.config.get("password"):
            if self.config.get("email"):
                Cloudjumper.cloudjumper_logger.info("[Need To Confirm Via Email \"{}\"!]".format(self.config.get("email")))
            self.register(self.config.get("password"), self.config.get("email"), True)
        if self.logged_in:
            for host in self.config.get("hosts", []):
                self.add_host(host)

    def is_command(self, command, message, need_nick=True):
        # Regex <3
        return bool(re.match("{}{}{}.*?".format(self.nick if need_nick else "",
                                             "!?\s" if need_nick else "",
                                             command),
                             message,
                             re.IGNORECASE))

    def cloudjumper_command(self, command, private_message=False, need_nick=True):
        def inner(func):
            @self.advanced_command(private_message)
            def more_inner(bot, message, sender):
                if bot.is_command(command, message, need_nick):
                    func(bot, message, sender)
                    return True

        return inner

    def apply_commands(self):
        origin = os.getcwd()
        for plugin_dict in Cloudjumper.plugins:
            for directory, plugin_list in plugin_dict.items():
                if os.path.isdir(directory):
                    os.chdir(directory)
                else:
                    continue

                if "*" in plugin_list:
                    while "*" in plugin_list:
                        plugin_list.remove("*")
                    plugin_list.extend(glob.glob("*.py"))

                Cloudjumper.cloudjumper_logger.debug("[Need To Load: '{}']".format(plugin_list))
                
                for plugin_name in plugin_list:
                    if plugin_name.endswith(".py"):
                        plugin_name = plugin_name[:-3]
                    try:
                        mod = (importlib.import_module(plugin_name))
                    except ImportError as e:
                        Cloudjumper.cloudjumper_logger.debug("[Failed To Load '{}' With Error '{}']".format(plugin_name, e))
                        continue

                    Cloudjumper.cloudjumper_logger.debug("[Loaded Plugin {}]".format(mod.__name__))
                    
                    handler_name = getattr(mod, "handler_name", "message_handler")
                    setup_name = getattr(mod, "setup_name", "setup_instance")

                    # If you don't want a setup_instance, that's fine.
                    if getattr(mod, setup_name, None) is not None:
                        getattr(mod, setup_name)(self)
                    
                    if getattr(mod, handler_name, None) is not None:
                        handler_func = getattr(mod, handler_name, False)
                        priv_msg = getattr(mod, "private_message", False)
                        if handler_func.__name__ == handler_name:
                            handler_func.__name__ = mod.__name__

                        self.advanced_command(priv_msg)(handler_func)         

                os.chdir(origin)

    def set_level(self, lvl=None):
        if self.config.get("debug"):
            super().set_level(logging.DEBUG)
            logging.getLogger(__name__).setLevel(logging.DEBUG)
        else:
            super().set_level(logging.INFO)
            logging.getLogger(__name__).setLevel(logging.INFO)

    def quit(self, message=None):
        if message is None:
            message = self.get_message("disconnect")
        super().quit(message)

    @classmethod
    def run_bot(cls, extra_settings={}):

        if not os.path.exists(cls.config_name):
            raise CloudjumperError("No such config file '{}'!".format(cls.config_name))
        else:
            with open(cls.config_name) as config_file:
                bot = cls(config_file, extra_settings)

            cls.cloudjumper_logger.debug("[Channel Commands: {}]".format(", ".join(i.__name__ for i in bot.channel_commands)))
            cls.cloudjumper_logger.debug("[Private Commands: {}]".format(", ".join(i.__name__ for i in bot.private_commands)))
            
            # Sometimes I just want to test if I've got syntax errors, or if my class doesn't __init__ correctly.
            # That's what this flag is used for.
            if not bot.config.get("kill"):
                try:
                    bot.run()
                except KeyboardInterrupt:
                    pass
                except (ConnectionResetError, BrokenPipeError) as e:
                    cls.cloudjumper_logger.debug("[Connection Failed With Error '{}', Exiting...]".format(e))
                finally:
                    if bot.started:
                        bot.quit(bot.get_message("disconnect"))



try:
    location = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1])
    with open(location + os.sep + "defaults.json") as default_file:
        Cloudjumper.defaults = json.load(default_file)
except FileNotFoundError as e:
    raise CloudjumperError("No defaults file was found!") from e
