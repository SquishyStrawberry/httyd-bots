#!/usr/bin/env python3

import os
import sys
import json
import praw
import praw.helpers
from _thread import start_new_thread

parent_directory = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-3])
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

import irc_helper


class Thornado(irc_helper.IRCBot):
    def __init__(self, config_file):
        needed = ("user", "nick", "channel", "host", "port")
        self.config = json.loads(config_file.read())
        self.subreddit = self.config.get("subreddit", "httyd")
        self.reddit = praw.Reddit(self.config.get("useragent", "Thornado"))
        super().__init__(**{k:v for k, v in self.config.items() if k in needed})
        start_new_thread(self.search_subreddit, tuple())

    def search_subreddit(self):
        for post in praw.helpers.submission_stream(self.reddit, self.subreddit, 1, 0):
            self.send_action(self.config.get("message",
                            "has spotted a new post on /r/{subreddit}! \"{title}\" by {submitter} | {link}").format
            (subreddit=self.subreddit, title=post.title, submitter=post.author.name, link="redd.it/" + post.id))
