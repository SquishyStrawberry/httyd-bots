#!/usr/bin/env python3

import re

private_message = False
name_needed = True
base = "https://reddit.com"

subreddit_finder = re.compile("(?:\s+|^)(/r/[a-zA-Z0-9_]+)(?:\s+|$)", re.IGNORECASE)


def message_handler(bot, message, sender):
    sub_match = subreddit_finder.match(message)
    if sub_match is not None:
        sub = sub_match.group(1)
        bot.send_action(bot.get_message("link_subreddit").format(link=base + sub))
        return True
