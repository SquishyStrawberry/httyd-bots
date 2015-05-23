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
parser.add_argument("-n", "--nick", type=str, help="What nickname to use.")
parser.add_argument("-u", "--user", type=str, help="What username to use.")
parser.add_argument("-d", "--database", type=str, help="What database to use", dest="database_name")
parser.add_argument("-k", "--kill", action="store_true", help="Do not start at all.")

argv = parser.parse_args()
argv_dict = argv.__dict__
argv_dict = {k: v for k, v in argv_dict.items() if v is not None}


Cloudjumper.run_bot(argv_dict)
