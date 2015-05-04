#!/usr/bin/env python3

import os
import sys

try:
    from thornado.thornado import Thornado
except ImportError:
    for i in range(1, 6):
        parent_directory = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-i])
        if parent_directory not in sys.path:
            sys.path.insert(0, parent_directory)
        try:
            from thornado.thornado import Thornado
        except ImportError:
            del sys.path[0]
        else:
            break
