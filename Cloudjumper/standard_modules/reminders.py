#!/usr/bin/env python3

private_message = False
name_needed = True

def command_handler(bot, message, str):
	if bot.is_command("blokes", message, name_needed):
		if bot.config.get("blokes_url"):
	        bot.send_action(bot.get_message("blokes_board").format(bot.config.get("blokes_url")))
	    else:
	        bot.send_action(bot.get_message("blokes_board_fail"))
	elif bot.is_command("location", message, name_needed):
	    if bot.config.get("github_location"):
	        bot.send_action(bot.get_message("location").format(bot.config.get("github_location")))
	    else:
	        bot.send_action(bot.get_message("location_fail"))
