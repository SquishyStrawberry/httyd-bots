#!/usr/bin/env python3

import os
import sys
import json
import praw
import praw.helpers
from _thread import start_new_thread

try:
    import irc_helper
except ImportError:
    for i in range(1, 6):
        parent_directory = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-i])
        if parent_directory not in sys.path:
            sys.path.insert(0, parent_directory)
        try:
            import irc_helper
        except ImportError:
            del sys.path[0]
        else:
            break


class Thornado(irc_helper.IRCBot):
    def __init__(self, config_file):
        needed = ("user", "nick", "channel", "host", "port")
        self.config = json.loads(config_file.read())
        self.messages = self.config.get("messages", {})
        self.subreddit = self.config.get("subreddit", "httyd")
        self.reddit = praw.Reddit(self.config.get("useragent", "Thornado"))
        super().__init__(**{k: v for k, v in self.config.items() if k in needed})
        start_new_thread(self.search_subreddit, tuple())

    def search_subreddit(self):
        for post in praw.helpers.submission_stream(self.reddit, self.subreddit, 1, 0):
            if self.started:
                self.send_action(self.messages.get("found_post",
                                                   "has spotted a new post on /r/{subreddit}! \"{title}\" by {submitter} | {link}").format
                                 (subreddit=self.subreddit, title=post.title, submitter=post.author.name,
                                  link="http://redd.it/" + post.id))
            else:
                return