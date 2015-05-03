#!/usr/bin/env python3
# Since Imports are based on sys.path, we need to add the parent directory.
import os
import re
import sqlite3
import sys
import time


parent_directory = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-2])
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

from irc_helper import IRCBot, IRCError

group_finder = re.compile("\(\?P<(.*?)>")


class IRCHelper(IRCBot):
    def __init__(self, database_name, response_delay=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_commands = set()
        self.private_commands = set()
        self.times = dict()
        self.response_delay = 3 if response_delay is None else response_delay
        self.command_database = sqlite3.connect(database_name)
        self.irc_cursor = self.command_database.cursor()
        self.irc_cursor.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
        tables = tuple(map(lambda x: x[0], self.irc_cursor.fetchall()))
        if "Commands" not in tables:
            self.irc_cursor.execute("CREATE TABLE Commands (id INTEGER PRIMARY KEY, trigger TEXT, response TEXT)")
        if "Flags" not in tables:
            self.irc_cursor.execute("CREATE TABLE Flags (id INTEGER PRIMARY KEY, username TEXT, flags TEXT)")

    # To add a command.
    # For commands that are functions.
    def advanced_command(self, private_message=False):
        return self.channel_commands.add if not private_message else self.private_commands.add

    # Use this if your function returns (trigger, command)
    def basic_command(self, *args, **kwargs):
        def basic_decorator(command):
            trigger, response = command(*args, **kwargs)
            self.irc_cursor.execute("SELECT * FROM Commands")
            if self.irc_cursor.fetchone() is None:
                self.irc_cursor.execute("INSERT INTO Commands VALUES (0,?,?)", (trigger, response))
            else:
                self.irc_cursor.execute("SELECT trigger FROM Commands WHERE trigger=? AND response=?",
                                        (trigger, response))
                if self.irc_cursor.fetchone() is None:
                    self.irc_cursor.execute("INSERT INTO Commands(trigger,response) VALUES (?,?)",
                                            (trigger, response))
            return command

        return basic_decorator

    def forget_basic_command(self, trigger):
        self.irc_cursor.execute("DELETE FROM Commands WHERE trigger=?", (trigger,))

    def since_last_comment(self, user):
        t = time.time() - self.times.get(user, 0)
        return 0 if t < 0 else t

    def handle_block(self, block):
        block_data = super().handle_block(block)
        if block_data.get("sender") != self.nick:
            if block_data.get("command", "").upper() == "PRIVMSG" and block_data.get("message"):
                if block_data.get("recipient").lower() == self.channel.lower():
                    command_list = self.channel_commands
                elif block_data.get("recipient").lower() == self.nick.lower():
                    command_list = self.private_commands
                else:
                    raise IRCError("Couldn't find commands to use! Recipient was '{}'".format(block_data.get("recipient")))


                for func_command in command_list:
                    if self.since_last_comment(block_data.get("sender")) < self.response_delay:
                        break
                    if func_command(self, block_data.get("message"), block_data.get("sender")):
                        self.times[block_data.get("sender", "")] = time.time()
                        break

                if block_data.get("recipient") == self.channel:
                    self.irc_cursor.execute("SELECT trigger,response FROM Commands")
                    for trigger, response in self.irc_cursor.fetchall():
                        if self.since_last_comment(block_data.get("sender")) < self.response_delay:
                            break
                        matched = re.search(trigger.format(nick=self.nick), block_data.get("message", ""), re.IGNORECASE)
                        if matched:
                            named_groups = {"${nick}": block_data.get("sender")}
                            new_response = response
                            for group_name in group_finder.findall(trigger):
                                named_groups["${" + group_name + "}"] = matched.group(group_name)
                            for group, value in named_groups.items():
                                new_response = new_response.replace(group, value)
                            self.send_action(new_response)
                            self.times[block_data.get("sender", "")] = time.time()


        return block_data  # Yes.

    def quit(self, message):
        self.started = False
        self.leave_channel(message)
        self.command_database.commit()
        self.command_database.close()
        self.socket.close()