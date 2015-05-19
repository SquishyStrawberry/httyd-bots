#!/usr/bin/env python3

import re
import requests

private_message = False
name_needed = True

# From Django
url_validator = re.compile(
    r"(^(?:(?:http|ftp)s?://)"  # http:// or https://
    r"((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/.+)?)", re.IGNORECASE)


def setup_instance(inst):
    inst.title_session = requests.Session()
    inst.title_session.headers.update({"User-Agent": "Py3 TitleFinder"})


def message_handler(bot, message, sender):
    url_match = url_validator.search(message.strip())
    if url_match is not None:
        url = url_match.group(1)
        req = bot.title_session.get(url)
        if req.ok:
            soup = BeautifulSoup(req.text)
            if soup.title is not None:
                bot.send_action(bot.get_message("urltitle").format(title=soup.title.text))
        return True
