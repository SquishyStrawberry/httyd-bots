#!/usr/bin/env python3
import os
import setuptools


if os.path.exists("requirements.txt"):
    with open("requirements.txt") as req_file:
        reqs = [i for i in req_file if i]
else:
    reqs = []

packs = setuptools.find_packages()


def setup():
    setuptools.setup(
        name="cloudjumper",
        version=1.0,
        description="A bot that can learn, attack, eat, etc... in IRC!",
        author="SquishyStrawberry",
        install_requires=reqs,
        packages=packs
    )

if __name__ == '__main__':
    setup()