#!/usr/bin/env python3

import re
import random

private_message = False
name_needed = True

diefinder = re.compile("(^|[1-9][0-9]*)d([1-9][0-9]*)$", re.IGNORECASE)


def message_handler(bot, message, sender):
	erred = False
	args = message.split(" ")

	if bot.is_command("roll", message, name_needed):
		
		if "dank" not in message:
			if len(args) >= int(name_needed) + 2:
				dice_data = diefinder.match(args[2])
				if dice_data is not None:
					amount, faces = int(dice_data.group(1) or "1"), int(dice_data.group(2))

					if amount <= bot.config.get("dice_maximum", 20) and faces <= bot.config.get("roll_maximum", 1024):
						rolls = [str(random.randint(1, faces)) for i in range(amount)]
						msg = bot.get_message("roll").format(result=", ".join(rolls), nick=sender)
						bot.send_action(msg)
						return True
					else:
						bot.send_action(bot.get_message("nodice").format(nick=sender))
						return True
		 
		else:
			bot.send_action(bot.get_message("dank_joke").format(nick=sender))

		bot.send_action(bot.get_message("diceerr").format(nick=sender))
		return True
