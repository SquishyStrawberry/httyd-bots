#!/usr/bin/env python3
import os
import setuptools
from thornado import __version__

if os.path.exists("requirements.txt"):
    with open("requirements.txt") as req_file:
        reqs = [i for i in req_file if i]
else:
    reqs = []

packs = setuptools.find_packages()

setuptools.setup(
    name="thornado",
    version=__version__,
    description="Bot that monitors subreddits and posts the posts to IRC.",
    author="SquishyStrawberry",
    install_requires=reqs,
    packages=packs
)
