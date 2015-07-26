#!/usr/bin/env python3
try:
    from cloudjumper.cloudjumper import Cloudjumper
except ImportError as e:
    try:
        import cloudjumper.cloudjumper
    except ImportError:
        pass
    else:
        raise e

__version__ = "2.3.3"

