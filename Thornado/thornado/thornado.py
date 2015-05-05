#!/usr/bin/env python3

import os
import sys
import json
import praw
import time
import threading

try:
    praw.helpers
except NameError:
    import praw.helpers

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

ONE_DAY = 1*60*60*24


class Thornado(irc_helper.IRCBot):
    def __init__(self, config_file, auto_start=True):
        needed = ("user", "nick", "channel", "host", "port")
        self.config = json.loads(config_file.read())
        self.messages = self.config.get("messages", {})
        try:
            with open(self.config.get("post_file")) as visited_file:
                self.posts = set(json.loads(visited_file.read()))
        except (FileNotFoundError, ValueError):
            self.posts = set()

        self.reddit = praw.Reddit(self.config.get("useragent", "Thornado"))
        self.subreddit = self.config.get("subreddit", "httyd").lower()

        super().__init__(**{k: v for k, v in self.config.items() if k in needed})

        self.thread = threading.Thread(target=self.search_subreddit, daemon=True)
        self.start = self.thread.start
        if auto_start:
            self.start()

    def search_subreddit(self):
        # noinspection PyUnresolvedReferences
        for post in praw.helpers.submission_stream(self.reddit, self.subreddit, 100, 0):
            post_time = time.time() - post.created
            if post and post.id not in self.posts and post.author and post_time < self.config.get("post_time", ONE_DAY):
                default = "\u0002has spotted a new post on /r/{subreddit}! \"{title}\" by {submitter} | {link}"
                message = self.messages.get("found_post", default)
                message = message.format(subreddit=self.subreddit,
                                         title=post.title,
                                         submitter=post.author.name,
                                         link="http://redd.it/" + post.id,
                                         post=post)
                                         # If you want anything else.
                self.send_action(message)
                self.posts.add(post.id)
                time.sleep(self.config.get("between_posts", 1))

    def quit(self, message):
        super().quit(message)
        with open(self.config.get("post_file"), "w") as visited_file:
            visited_file.write(json.dumps(list(self.posts)))
