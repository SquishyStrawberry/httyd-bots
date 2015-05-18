#!/usr/bin/env python3
import logging
import os
import random
import re
import requests
import json
import irc_helper
from bs4 import BeautifulSoup


# From Django
url_validator = re.compile(
    r"(^(?:(?:http|ftp)s?://)"  # http:// or https://
    r"((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/.+)?)", re.IGNORECASE)

subreddit = re.compile("(?:\s+|^)/r/([a-zA-Z0-9_]+)(?:\s+|$)", re.IGNORECASE)
cloudjumper_logger = logging.getLogger(__name__)


class CloudjumperError(irc_helper.IRCError):
    pass


# noinspection PyUnusedLocal
class Cloudjumper(irc_helper.IRCHelper):
    flags = {
        "admin": "a",
        "superadmin": "s",
        "whitelist": "w",
        "ignore": "i",
        "fantastic": "f",
    }
    defaults = None
    config_name = "config.json"
    # Hard coded on purpose.
    excluded_nicknames = ("skullcrusher", "thornado")

    def __init__(self, config_file, extra_settings={}):
        super_args = \
            ("user", "nick", "channel",
             "host", "port", "database_name",
             "response_delay", "fail_after", "check_login",
             "use_ssl")

        self.config_file = config_file
        self.config = json.loads(self.config_file.read())
        self.config.update(extra_settings)
        self.messages = self.config.get("messages", {})
        self.set_level()
        real_config = {k: v for k, v in self.config.items() if k in super_args}
        keys = tuple(real_config.keys())
        for setting in super_args:
            if setting not in keys:
                raise CloudjumperError("Invalid Settings! Setting '{}' was not provided!".format(setting))

        super().__init__(**real_config)

        if self.nick not in self.config.get("inedible_victims", []):
            self.config.get("inedible_victims", []).append(self.nick.lower())

        self.irc_cursor.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
        tables = tuple(map(lambda x: x[0], self.irc_cursor.fetchall()))
        if "Stomach" not in tables:
            self.irc_cursor.execute("CREATE TABLE Stomach (id INTEGER PRIMARY KEY, thing TEXT, real_thing TEXT)")
        if "Whispers" not in tables:
            self.irc_cursor.execute(
                "CREATE TABLE Whispers (id INTEGER PRIMARY KEY, user TEXT, message TEXT, sender TEXT)")
        self.apply_commands()
        self.add_flag("superadmin", "MysteriousMagenta")
        self.add_flag("superadmin", self.nick)

        for user in self.config.get("awesome_people", []):
            self.add_flag("fantastic", user)

        for setting in self.config.get("auto_admin", []):
            self.add_flag("superadmin", setting)

        self.irc_cursor.execute("SELECT username FROM Flags WHERE flags LIKE \"%s%\"")
        for (user,) in self.irc_cursor.fetchall():
            self.add_flag("admin", user)
            self.add_flag("whitelist", user)


    def extra_handling(self, block_data):
        # noinspection PyUnresolvedReferences
        if block_data.get("sender", "").lower() in Cloudjumper.excluded_nicknames:
            return block_data
        block_data = super().extra_handling(block_data)
        if block_data.get("command", "").upper() == "JOIN":
            if not self.has_flag("ignore", block_data.get("sender")):
                if not self.has_flag("fantastic", block_data.get("sender")):
                    greeting = random.choice(self.get_message("greetings")).format(nick=block_data.get("sender"))
                else:
                    greeting = random.choice(self.get_message("awesome_greetings")).format(
                        nick=block_data.get("sender"))
                self.send_action(greeting)

        if block_data.get("sender") == "Toothless" and block_data.get("recipient") == self.nick:
            try:
                trigger, response = block_data.get("message", "").split("->", 1)
            except ValueError:
                # Signifies that the message is not a command.
                pass
            else:
                @self.basic_command()
                def dummy():
                    return trigger, response

        if self.since_last_comment(block_data.get("sender", "")) < self.response_delay:
            return block_data

        if block_data.get("recipient") == self.channel and block_data.get("sender"):

            self.irc_cursor.execute("SELECT message,sender FROM Whispers WHERE user=?",
                                    (block_data.get("sender").lower(),))
            messages = self.irc_cursor.fetchall()
            if messages:
                self.send_message(self.get_message("announce_mail").format(nick=block_data.get("sender")))
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
                cloudjumper_logger.info("[Need To Confirm Via Email \"{}\"!]".format(self.config.get("email")))
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
            url = url_match.group(1)
            req = requests.get(url, headers={"User-Agent": "Py3 TitleFinder"})
            if req.ok:
                soup = BeautifulSoup(req.text)
                title = soup.title
                if title is not None:
                    cloudjumper_logger.debug("[Opened URL '{}' With Title '{}']".format(url, title.text))
                    bot.send_action(self.get_message("urltitle").format(title=title.text))
                else:
                    bot.send_action(self.get_message("urltitle_fail"))
                # TODO Implement proper Youtube API
            else:
                cloudjumper_logger.debug("[Failed To Get Title Of URL '{}']".format(url))
                bot.send_action(self.get_message("urltitle_fail"))
            return True

        @self.cloudjumper_command("learn")
        def learn_trigger(bot: Cloudjumper, message: str, sender: str):
            args = [i for i in message.split("->", 1) if i]
            if len(args) >= 2:
                if bot.has_flag("whitelist", sender) or bot.has_flag("admin", sender) or bot.has_flag("superadmin",
                                                                                                      sender):
                    trigger, response = message.split(" ", 2)[2].split("->", 1)
                    trigger, response = trigger.strip(), response.strip()
                    cloudjumper_logger.debug("[Learnt {} -> {}]".format(trigger, response))
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

        @self.cloudjumper_command("forget")
        def forget_trigger(bot: Cloudjumper, message: str, sender: str):
            if len(message.split(" ")) >= 3:
                if bot.has_flag("whitelist", sender) or bot.has_flag("admin", sender) or bot.has_flag("superadmin",
                                                                                                      sender):
                    trigger = message.split(" ", 2)[2].strip()
                    cloudjumper_logger.debug("[Forgot {}]".format(trigger))
                    bot.irc_cursor.execute("SELECT response FROM Commands WHERE trigger=?", (trigger,))
                    response = (bot.irc_cursor.fetchone() or [None])[0]
                    if response is not None:
                        bot.send_action(self.get_message("forget").format(nick=sender))
                        bot.forget_basic_command(trigger)
                    else:
                        bot.send_action(self.get_message("forget_superfluous").format(nick=sender))
                else:
                    bot.send_action("doesn't want to be trained by {nick}!".format(nick=sender))
            return len(message.split(" ")) >= 3

        @self.cloudjumper_command("attack")
        def attack(bot: Cloudjumper, message: str, sender: str):
            if len(message.split(" ")) >= 3:
                chosen_attack = random.choice(bot.get_message("attacks"))
                victim = message.split(" ", 2)[2]
                if "{target}" in chosen_attack:
                    chosen_attack = chosen_attack.format(target=victim)
                else:
                    chosen_attack += victim
                bot.send_action(chosen_attack)
            return len(message.split(" ")) >= 3

        @self.cloudjumper_command("eat")
        def eat(bot: Cloudjumper, message: str, sender: str):
            if len(message.split(" ")) >= 3:
                victim = message.split(" ", 2)[2]
                if victim.lower() not in map(lambda x: x.lower(), bot.config.get("inedible_victims", [])):
                    self.irc_cursor.execute("SELECT thing FROM Stomach")
                    stomach = self.irc_cursor.fetchall()
                    if victim not in stomach:
                        bot.send_action(self.get_message("eat").format(victim=victim))
                        bot.irc_cursor.execute("SELECT * FROM Stomach")
                        if not bot.irc_cursor.fetchone():
                            bot.irc_cursor.execute("INSERT INTO Stomach VALUES (0,?,?)", (victim.lower(), victim))
                        else:
                            bot.irc_cursor.execute("INSERT INTO Stomach(thing,real_thing) VALUES (?,?)",
                                                   (victim.lower(), victim))
                    else:
                        bot.send_action(bot.get_message("eat_superfluous"))
                else:
                    bot.send_action(self.get_message("eat_inedible").format(victim=victim))
            return len(message.split(" ")) >= 3

        @self.cloudjumper_command("spit")
        def spit(bot: Cloudjumper, message: str, sender: str):
            if len(message.split(" ")) >= 3:
                victim = message.split(" ", 2)[2]
                bot.irc_cursor.execute("SELECT * FROM Stomach WHERE thing=?", (victim.lower(),))
                if bot.irc_cursor.fetchone():
                    # noinspection PyUnresolvedReferences
                    bot.irc_cursor.execute("DELETE FROM Stomach WHERE thing=?", (victim.lower(),))
                    bot.send_action("spits out {}!".format(victim))
                else:
                    bot.send_action("hasn't eaten {} yet!".format(victim))
            return len(message.split(" ")) >= 3

        @self.cloudjumper_command("stomach")
        def show_stomach(bot: Cloudjumper, message: str, sender: str):
            self.irc_cursor.execute("SELECT real_thing FROM Stomach")
            stomach = self.irc_cursor.fetchall()
            if stomach:
                stomachs = ", ".join(map(lambda x: x[0], stomach))
                bot.send_action(bot.get_message("stomach").format(victims=stomachs))
            else:
                bot.send_action(bot.get_message("stomach_empty"))
            return True

        @self.cloudjumper_command("vomit")
        def vomit(bot: Cloudjumper, message: str, sender: str):
            bot.irc_cursor.execute("SELECT * FROM Stomach")
            if bot.irc_cursor.fetchone():
                bot.send_action(self.get_message("vomit"))
                bot.irc_cursor.execute("DELETE FROM Stomach")
            else:
                bot.send_action(self.get_message("vomit_superfluous"))
            return True

        @self.cloudjumper_command("roll")
        def roll_dice(bot: Cloudjumper, message: str, sender: str):
            erred = False
            if "dank" in message:
                bot.send_action(bot.get_message("dank_joke").format(nick=sender))
                return True
            if len(message.split(" ")) >= 3:
                die = message.split(" ")[2].split("d")
                if len(die) == 1:
                    die = ["1"] + die
                amount, maximum = die
                if not amount.isdigit() or not maximum.isdigit():

                    bot.send_action(bot.get_message("diceerr").format(nick=sender))
                else:
                    amount, maximum = int(amount), int(maximum)
                    if bot.config.get("roll_maximum", -1) > -1 and not bot.has_flag("admin", sender):
                        if maximum > bot.config.get("roll_maximum", -1) or maximum < 1:
                            bot.send_action(bot.get_message("nodice").format(nick=sender))
                            erred = True
                    if bot.config.get("dice_maximum", -1) > -1 and not bot.has_flag("admin", sender):
                        if amount > bot.config.get("dice_maximum", -1) or amount < 1:
                            bot.send_action(bot.get_message("nodice").format(nick=sender))
                            erred = True
                    if not erred:
                        if maximum > 1:
                            rolls = [str(random.randint(1, maximum)) for _ in range(amount)]
                        else:
                            rolls = [("2" if random.randint(1, 100) in random.sample(range(1, 101), 10) else "1")
                                     for _ in range(amount)]
                        if rolls:
                            bot.send_action(bot.get_message("roll").format(nick=sender, result=", ".join(rolls)))
                        else:
                            bot.send_action(bot.get_message("diceerr").format(nick=sender))
            else:
                bot.send_action(bot.get_message("diceerr").format(nick=sender))
            return True

        @self.cloudjumper_command("purge_commands", True, False)
        def clear_commands(bot: Cloudjumper, message: str, sender: str):
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

        @self.cloudjumper_command("terminate", True, False)
        def terminate(bot: Cloudjumper, message: str, sender: str):
            if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                bot.log("[Terminating...]")
                bot.quit(bot.get_message("disconnect"))
            else:
                bot.send_action(bot.get_message("deny_command"), sender)
            return True

        @self.cloudjumper_command("terminate")
        def terminate_channel(bot: Cloudjumper, message: str, sender: str):
            if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                bot.log("[Terminating...]")
                bot.quit(bot.get_message("disconnect"))
            else:
                bot.send_action(bot.get_message("deny_command"))
            return True

        @self.cloudjumper_command("list_commands", True, False)
        def list_commands(bot: Cloudjumper, message: str, sender: str):
            bot.irc_cursor.execute("SELECT trigger,response FROM Commands")
            comms = bot.irc_cursor.fetchall()
            if comms:
                for trigger, response in comms:
                    bot.send_message(
                        bot.get_message("print_command").format(trigger=trigger,
                                                                 response=response),
                        sender)
            else:
                bot.send_action(bot.get_message("no_commands"))
            return True

        @self.cloudjumper_command("copy_original", True, False)
        def copy_original(bot: Cloudjumper, message: str, sender: str):
            if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                bot.copying = True
                bot.send_action(self.get_message("copy_original"), sender)
                bot.send_message("list_commands", "Toothless")

            else:
                bot.send_action(bot.get_message("deny_command"), sender)
            return True

        @self.cloudjumper_command("add_flag", True, False)
        def add_flag_pm(bot: Cloudjumper, message: str, sender: str):
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

        @self.cloudjumper_command("remove_flag", True, False)
        def rm_flag_pm(bot: Cloudjumper, message: str, sender: str):
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

        @self.cloudjumper_command("reload_config", True, False)
        def reload_config(bot: Cloudjumper, message: str, sender: str):
            if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                if not bot.config_file.closed:
                    bot.config_file.close()
                bot.config_file = open(bot.config_file.name, bot.config_file.mode)
                bot.config = json.loads(bot.config_file.read())
                bot.messages = bot.config.get("messages", {})
                bot.send_action(bot.get_message("config_reloaded"), sender)
                try:
                    default_path = os.path.abspath(__file__).split(os.sep)[:-1] + os.sep + "defaults.json"
                    with open(os.sep.join(default_path)) as default_file:
                        bot.__class__.defaults = json.loads(default_file.read())
                except NameError:
                    # If this gets compiled with cx_freeze, we won't have __file__
                    bot.send_action(bot.get_message("fail_defaults"), sender)
            else:
                bot.send_action(bot.get_message("deny_command"), sender)
            return True

        @self.cloudjumper_command("move_channel", True, False)
        def move_channel(bot: Cloudjumper, message: str, sender: str):
            if bot.has_flag("admin", sender) or bot.has_flag("superadmin", sender):
                channel = message.split(" ")[1].lower()
                bot.leave_channel(bot.get_message("switch_channel"))
                bot.join_channel(channel)

            else:
                bot.send_action(bot.get_message("deny_command"), sender)
            return True

        @self.cloudjumper_command("ignore_me", True, False)
        def ignore_me(bot: Cloudjumper, message: str, sender: str):
            if not bot.has_flag("ignore", sender):
                cloudjumper_logger.debug("[Started Ignoring '{}']".format(sender))
                bot.add_flag("ignore", sender)
                bot.send_action(bot.get_message("ignore"), sender)
            else:
                cloudjumper_logger.debug("['{}' Asked To Be Ignored, But Was Already Being Ignored.]".format(sender))
                bot.send_action(bot.get_message("ignore_superfluous"), sender)

        @self.cloudjumper_command("tell")
        def tell_user(bot: Cloudjumper, message: str, sender: str):
            user, whisper = message.split(" ", 3)[2:]
            user = user.lower()
            cloudjumper_logger.debug("[Registered Message '{}' From '{}' To '{}']".format(whisper, sender, user))
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

        @self.advanced_command(False)
        def link_subreddit(bot: Cloudjumper, message: str, sender: str):
            subreddit_name = subreddit.search(message)
            if subreddit_name:
                short_link = "/r/" + subreddit_name.group(1)
                link = "https://www.reddit.com" + short_link
                cloudjumper_logger.debug("[Linked Subreddit '{}']".format(short_link))
                bot.send_action(bot.get_message("link_subreddit").format(link=link))


        @self.cloudjumper_command("blokes")
        def bloke_board(bot: Cloudjumper, message:str, sender:str):
            if bot.config.get("blokes_url"):
                bot.send_action(bot.get_message("blokes_board").format(bot.config.get("blokes_url")))
            else:
                bot.send_action(bot.get_message("blokes_board_fail"))

        @self.cloudjumper_command("location")
        def git_location(bot: Cloudjumper, message: str, sender: str):
            if bot.config.get("github_location"):
                bot.send_action(bot.get_message("location").format(bot.config.get("github_location")))
            else:
                bot.send_action(bot.get_message("location_fail"))


    def set_level(self, lvl=None):
        if self.config.get("debug"):
            super().set_level(logging.DEBUG)
            logging.getLogger(__name__).setLevel(logging.DEBUG)
        else:
            super().set_level(logging.INFO)
            logging.getLogger(__name__).setLevel(logging.INFO)

    @classmethod
    def run_bot(cls, extra_settings={}):

        if not os.path.exists(cls.config_name):
            raise CloudjumperError("No such config file '{}'!".format(cls.config_name))
        else:
            with open(cls.config_name) as config_file:
                # noinspection PyCallingNonCallable
                bot = cls(config_file, extra_settings)


            try:
                bot.run()
            except KeyboardInterrupt:
                pass
            finally:
                if bot.started:
                    bot.quit(bot.get_message("disconnect"))



try:
    with open(os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1]) + os.sep + "defaults.json") as default_file:
        Cloudjumper.defaults = json.loads(default_file.read())
except FileNotFoundError as e:
    raise CloudjumperError("No defaults file was found!") from e

if __name__ == "__main__":
    print("You are trying to run cloudjumper.py to run the bot, "
          "but instead you need to run -m cloudjumper.")
