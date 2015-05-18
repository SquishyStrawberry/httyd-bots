#!/usr/bin/env python3
import argparse
from cloudjumper import Cloudjumper

parser = argparse.ArgumentParser(__name__)

# We can't have SSL/Debug argparser args mostly because they are bools.
# I could figure a way out, though.
parser.add_argument("-s", "--server", type=str, help="What server to connect to.")
parser.add_argument("-c", "--channel", type=str, help="What channel to connect to.")
parser.add_argument("-p", "--port", type=int, help="What port to connect on")
parser.add_argument("-H", "--host", type=str, help="What server to connect to.")
parser.add_argument("-P", "--password", type=str, help="What password to use.")
parser.add_argument("-e", "--email", type=str, help="What email to login with.")


argv = parser.parse_args()
argv_dict = argv.__dict__
argv_dict = {k: v for k, v in argv_dict.items() if k is not None}

Cloudjumper.run_bot()
