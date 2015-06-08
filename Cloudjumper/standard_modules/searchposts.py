#!/usr/bin/env python3
import praw
from requests.exceptions import HTTPError

name_needed = True
private_message = False


def setup_instance(inst):
    user_agent = inst.config.get("user_agent",
                                 "Python3 DragonHelper")
    inst.reddit = praw.Reddit(user_agent)

def message_handler(bot, message, sender):
    args = message.split(" ")
    if bot.is_command("reddit", message, name_needed):
        if len(args) >= int(name_needed)+2:
            sub = args[int(name_needed)+1]
            if "/" in sub:
                if sub.count("/") > 1:
                    bot.send_action(bot.get_message("command_error").format(nick=sender))
                else:
                    sub, comment = sub.split("/")
            else:
                comment = None    
            try:
                thing = bot.reddit.get_submission(submission_id=sub)
            except HTTPError:
                thing = None
            if thing is not None:
                if comment is not None:
                    comments = thing.comments
                    comments = praw.helpers.flatten_tree(comments)
                    actual_comment = None
                    for n, i in enumerate(comments):
                        if getattr(i, "id", None) == comment:
                            actual_comment = n
                            break

                    if actual_comment is not None:
                        actual_comment = comments[actual_comment]
                        bot.send_action(bot.get_message("comment_found").format(actual_comment))
                    else:
                        bot.send_action(bot.get_message("comment_not_found").format(comment))
                else:
                    bot.send_action(bot.get_message("post_found").format(thing))
            else:
                bot.send_action(bot.get_message("post_not_found").format(sub))
        else:
            bot.send_action(bot.get_message("command_error").format(nick=sender))
        return True

