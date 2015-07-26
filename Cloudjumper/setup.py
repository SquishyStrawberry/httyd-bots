#!/usr/bin/env python3
import os
import setuptools
from cloudjumper import __version__


reqs = [
    "beautifulsoup4",
    "requests",
    "irc_helper",
    "praw"
]

packs = setuptools.find_packages()


def setup():
    setuptools.setup(
        name="cloudjumper",
        version=__version__,
        description="A bot that can learn, attack, eat, etc... in IRC!",
        author="SquishyStrawberry",
        install_requires=reqs,
        packages=packs,
        package_data={
            "cloudjumper": ["defaults.json"]
        }
    )

if __name__ == "__main__":
    setup()
