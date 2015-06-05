#!/usr/bin/env python3
try:
    from thornado.thornado import Thornado
except ImportError as e:
    try:
        import thornado.thornado
    except ImportError:
        pass
    else:
        raise e

__version__ = "1.3.4"

