#!/usr/bin/env python3

import re
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError

private_message = False
name_needed = True

# From Django
url_validator = re.compile(
    r"((?:(?:http|ftp)s?://)"  # http:// or https://
    r"([A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?|"  # domain...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/.+)?)", re.IGNORECASE)


def setup_instance(inst):
    inst.title_session = requests.Session()
    inst.title_session.headers.update({"User-Agent": "Py3 TitleFinder"})


def message_handler(bot, message, sender):
    url_match = url_validator.search(message.strip())
    if url_match is not None:
        url, domain = url_match.group(1, 2)
        domain = domain.rstrip(".")
        # Mis-spelled on purpose.
        bite_size = bot.config.get("byte_amount", {}).get(domain, 2048)
        try:    
            req = bot.title_session.get(url,
                                        stream=True, 
                                        timeout=bot.config.get("request_timeout", 10))
        except ConnectionError:
            pass
        else:
            if req.ok:
                soup = BeautifulSoup(next(req.iter_content(bite_size)))
                if soup.title is not None:
                    title = soup.title.text.strip()
                    # No useless titles.
                    if title.lower() != domain.lower():
                        bot.send_action(bot.get_message("urltitle").format(title=title))
            req.close()
        return True
