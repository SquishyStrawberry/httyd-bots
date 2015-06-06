#!/usr/bin/env python3

import json
import logging
import os
import time
import threading

import praw
import praw.helpers
import irc_helper


ONE_DAY = 1 * 60 * 60 * 24
TEN_MINUTES = 1 * 60 * 10
thornado_logger = logging.getLogger(__name__)


class ThornadoError(Exception):
    pass


class Thornado(irc_helper.IRCBot):
    config_name = "config.json"
    validation = [
        "id",
        "author",
        "created",
        "title",
        "subreddit",
    ]

    def __init__(self, config_file, auto_start=True, extra_settings={}):
        needed = ("user", "nick", "channel", "host", "port", "use_ssl")
        self.config = json.load(config_file)
        self.config.update(extra_settings)
        self.messages = self.config.get("messages", {})
        if os.path.exists(self.config.get("post_file")):
            with open(self.config.get("post_file")) as visited_file:
                try:
                    self.posts = set(json.loads(visited_file.read()))
                except ValueError:
                    self.posts = set()
        else:
            self.posts = set()

        self.reddit = praw.Reddit(self.config.get("useragent", "Thornado"))
        self.subreddit = self.config.get("subreddit", "httyd").lower()

        super().__init__(**{k: v for k, v in self.config.items() if k in needed})

        if self.config.get("password"):
            self.register(self.config.get("password"), self.config.get("email"), True)

        self.thread = threading.Thread(target=self.search_subreddit)
        self.thread.daemon = True
        self.start = self.thread.start

        if auto_start:
            self.start()

    def search_subreddit(self):
        """
        Not intended for use outside of the internal thread.
        Searches self.subreddit for new posts, and posts them to self.channel
        """
        default = "\u0002has spotted a new post on /r/{subreddit}! \"{title}\" by {submitter} | {link}"
        base_message = self.messages.get("found_post", default)
        while True:
            posts = self.reddit.get_subreddit(self.subreddit).get_new()
            posts = filter(self.is_valid, posts)
            for post in posts:
                message = base_message.format(subreddit=post.subreddit,
                                              title=post.title,
                                              submitter=post.author.name,
                                              link="http://redd.it/" + post.id,
                                              post=post)
                thornado_logger.debug("[Found A Post '{}']".format(post.id))
                self.send_action(message)
                self.posts.add(post.id)
                time.sleep(self.config.get("between_posts", 1))
            time.sleep(self.config.get("between_checks", TEN_MINUTES))

    def quit(self, message):
        super().quit(message)
        thornado_logger.debug("[Quitting with list of posts {}]".format(self.posts))
        with open(self.config.get("post_file"), "w") as visited_file:
            json.dump(list(self.posts), visited_file, indent=2)

    def set_level(self, lvl=None):
        if self.config.get("debug"):
            super().set_level(logging.DEBUG)
            thornado_logger.setLevel(logging.DEBUG)
        else:
            super().set_level(logging.INFO)
            thornado_logger.setLevel(logging.DEBUG)

    def join_channel(self, channel):
        super().join_channel(channel)
        self.send_action(self.messages.get("join", "flies in"))

    def is_valid(self, post):
        # Sanity check.
        if all(getattr(post, i, None) for i in Thornado.validation):
            # Posted in the time limit.
            if time.time() - post.created <= self.config.get("post_time", ONE_DAY):
                # Not posted before
                if post.id not in self.posts:
                    return True
        return False

    @classmethod
    def run_bot(cls, extra_settings={}):
        if not os.path.exists(cls.config_name):
            raise ThornadoError("Couldn't find Config File!")
        with open(cls.config_name) as config_file:
            bot = cls(config_file, extra_settings=extra_settings)

        try:
            bot.run()
        except KeyboardInterrupt:
            pass
        finally:
            # It really isn't worth it to make a bot.get_message
            bot.quit(bot.messages.get("disconnect",
                                      "Gotta go feed my little Thornados."))
