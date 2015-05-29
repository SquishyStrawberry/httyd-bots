#!/usr/bin/env python3
import random


private_message = False
name_needed = True

# This might be obvious, but basically it's who beats who.
# value = beater of key.
pairs = {
    "rock": "paper",
    "paper": "scissors",
    "scissors": "rock"
}

def message_handler(bot, message, sender):
    args = message.split(" ")
    if bot.is_command("play", message, name_needed):
        if len(args) < int(name_needed)+2 or args[int(name_needed)+1].lower() not in pairs:
            bot.send_action(bot.get_message("command_error").format(nick=sender))
        else:
            move = args[int(name_needed)+1].lower()
            # tuple(pairs) == tuple(pairs.keys())
            # (can't index a .keys() object)
            bot_move = random.choice(tuple(pairs))
            if bot_move == pairs[move]:
                bot.send_action(bot.get_message("rps_win").format(nick=sender, bot_move=bot_move, user_move=move))
            elif bot_move == move:
                bot.send_action(bot.get_message("rps_tie").format(nick=sender, bot_move=bot_move, user_move=move))
            else:
                bot.send_action(bot.get_message("rps_loss").format(nick=sender, bot_move=bot_move, user_move=move))
