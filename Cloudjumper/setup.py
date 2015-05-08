#!/usr/bin/env python3
import setuptools

with open("requirements.txt") as req_file:
    reqs = req_file.read().splitlines()

packs = [

]
scripts = [
    "cloudjumper/cloudjumper.py"
]

setuptools.setup(
    name="cloudjumper",
    version="1.0",
    packages=packs,
    scripts=scripts,
    install_requires=reqs,
    description="Simple IRC Bot that can learn, attack, etc...",
)