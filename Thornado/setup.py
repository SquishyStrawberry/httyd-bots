#!/usr/bin/env python3
import setuptools

with open("requirements.txt") as req_file:
    reqs = req_file.read().splitlines()

packs = [

]
scripts = [
    "thornado/thornado.py"
]

setuptools.setup(
    name="thornado",
    version="1.0",
    packages=packs,
    scripts=scripts,
    install_requires=reqs,
    description="Bot that can monitor subreddits and post them in IRC.",
)