#!/usr/bin/env python3
"""
Small file that handles IRC Handling.
Currently doesn't comply with RFC section 2.3.1, but it'll get there.
I just have to find out the freaking format :/
"""
import socket


class IRCError(Exception):
    pass


class IRCBot(object):
    def __init__(self, user, nick, channel, host, port=6667):
        self.connection_data = (host, port)
        self.user = user
        self.nick = nick
        self.base_channel = channel
        self.channel = None
        self.started = False
        self.log = print
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.connection_data)
        self.start_up()

    def start_up(self):
        while True:
            block = self.get_block()
            if self.handle_ping(block):
                continue
            elif "nickname is already in use" in block.lower():
                raise IRCError("Nickname '{}' is already in use!".format(self.nick))
            elif "found your hostname" in block.lower():
                self.socket.send("USER {0} 0 * :{0}\r\n".format(self.user).encode())
                self.socket.send("NICK {}\r\n".format(self.nick).encode())
            elif "end of /motd" in block.lower():
                self.started = True
                return

    def join_channel(self, channel):
        self.channel = channel
        self.socket.send("JOIN {}\r\n".format(channel).encode())

    def get_block(self):
        message = b""
        while not (b"\n" in message and b"\r" in message):
            message += self.socket.recv(1)
        return message.decode()

    def send_message(self, message, send_to=None):
        if send_to is None:
            if self.channel is None:
                raise IRCError("Tried calling send_message without being in a channel and with no recipient!")
            send_to = self.channel
        self.log("[{} {} {}] {}".format(self.nick, "on" if send_to == self.channel else "to", send_to, message))
        self.socket.send("PRIVMSG {} :{}\r\n".format(send_to, message).encode())

    def send_action(self, message, send_to=None):
        self.send_message("\u0001ACTION \x0303{}\u0001".format(message), send_to)

    def handle_block(self, block):
        message_parts = block.split(" ", 1)
        sender = message_parts[0][1:].split("!", 1)[0]
        command = message_parts[1].strip()
        if "(Throttled: Reconnecting too fast)" in block:
            raise IRCError("Reconnecting too fast!")
        if self.handle_ping(block):
            return {"command": "PING", "message": command[1:]}
        if sender in (self.nick, self.user) or sender == self.connection_data[0]:
            return {"sender": self.connection_data[0]}

        message_info = command.split(" ", 2)
        command, recipient = message_info[:2]
        if len(message_info) >= 3:
            message = message_info[2][1:]
        else:
            message = ""

        # Are there any other commands I need to handle?
        if command.upper() in ("PRIVMSG", "ALERT"):
            self.log("[{} to {}] {}".format(sender, recipient, message))
        return {"command": command, "sender": sender, "recipient": recipient, "message": message}

    def handle_ping(self, message):
        is_ping = message.upper().startswith("PING")
        if is_ping:
            self.log("[+] Received Ping!")
            data = "".join(message.split(" ", 1)[1:])[1:]
            self.socket.send("PONG :{}\r\n".format(data).encode())
        return is_ping

    def leave_channel(self, message=None):
        quit_message = (" :" + message) if message is not None else None
        self.socket.send("PART {}{}\r\n".format(self.channel, quit_message or "").encode())

    def run(self):
        while self.started:
            if self.started and self.channel is None:
                self.join_channel(self.base_channel)
            msg = self.get_block()
            self.handle_block(msg)

    def quit(self, message):
        self.leave_channel(message)
        self.started = False
        self.socket.close()