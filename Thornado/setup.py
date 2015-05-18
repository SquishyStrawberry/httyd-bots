#!/usr/bin/env python3
import os
import setuptools

if os.path.exists("requirements.txt"):
    with open("requirements.txt") as req_file:
        reqs = [i for i in req_file if i]
else:
    reqs = []

packs = setuptools.find_packages()
if not packs:
    raise Exception("Couldn't find any packages!")


def setup():
    setuptools.setup(
        name="thornado",
        version=1.2,
        description="Bot that monitors subreddits and posts the posts to IRC.",
        author="SquishyStrawberry",
        install_requires=reqs,
        packages=packs
    )

if __name__ == "__main__":
    setup()