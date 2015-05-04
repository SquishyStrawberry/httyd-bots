#!/usr/bin/env python3

import os
import sys
import json
import praw
import praw.helpers
import sqlite3
import queue
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

def clean_table_name(raw):
    return "".join(c for c in raw if c.isalnum())

class Thornado(irc_helper.IRCBot):
    def __init__(self, config_file):
        needed = ("user", "nick", "channel", "host", "port")
        self.config = json.loads(config_file.read())
        self.messages = self.config.get("messages", {})

        self.post_database = sqlite3.connect(self.config.get("database_name", "subreddits.db"))
        self.post_cursor = self.post_database.cursor()

        self.subreddit = self.config.get("subreddit", "httyd")
        self.table_name = clean_table_name(self.subreddit.capitalize())

        self.posts = {}
        self.queue = queue.Queue()

        self.reddit = praw.Reddit(self.config.get("useragent", "Thornado"))
        super().__init__(**{k: v for k, v in self.config.items() if k in needed})

        self.post_cursor.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
        tables = tuple(map(lambda x: x[0], self.post_cursor.fetchall()))
        if self.table_name not in tables:
            self.post_cursor.execute("CREATE TABLE {} (id INTEGER PRIMARY KEY, post TEXT)".format(self.table_name))

        self.update_posts()
        start_new_thread(self.search_subreddit, tuple())

    def search_subreddit(self):
       for post in praw.helpers.submission_stream(self.reddit, self.subreddit, 1, 0):
            print(self.posts)
            if post.id not in self.posts:
                self.send_action(self.messages.get("found_post",
                                                   "has spotted a new post on /r/{subreddit}! \"{title}\" by {submitter} | {link}").format
                                 (subreddit=self.subreddit, title=post.title, submitter=post.author.name,
                                  link="http://redd.it/" + post.id))
                self.queue.put(post.id)
            if not self.started:
                return

    def handle_block(self, block):
        super().handle_block(block)
        self.add_post()

    def add_post(self):
        self.update_posts()
        post_id = self.queue.get()
        if post_id and post_id not in self.posts:
            if not self.posts:
                self.post_cursor.execute("INSERT INTO {} VALUES (0,?)".format(self.table_name), (post_id,))
            else:
                self.post_cursor.execute("INSERT INTO {}(post) VALUES (?)".format(self.table_name), (post_id,))
        self.queue.task_done()

    def update_posts(self):
        self.post_cursor.execute("SELECT post FROM {}".format(self.table_name))
        posts = tuple(map(lambda x: x[0], self.post_cursor.fetchall()))
        self.posts = set(posts)

    def quit(self, message):
        super().quit(message)
        while not self.queue.all_tasks_done:
            self.add_post()
        self.post_database.commit()
        self.post_database.close()
