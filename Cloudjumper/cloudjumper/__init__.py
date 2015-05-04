#!/usr/bin/env python3

import os
import sys

try:
    from cloudjumper.cloudjumper import Cloudjumper
except ImportError:
    for i in range(1, 6):
        parent_directory = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-i])
        if parent_directory not in sys.path:
            sys.path.insert(0, parent_directory)
        try:
            from cloudjumper.cloudjumper import Cloudjumper
        except ImportError:
            del sys.path[0]
        else:
            break