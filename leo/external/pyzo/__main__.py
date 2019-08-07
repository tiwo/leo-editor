#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Pyzo __main__ module

This module takes enables starting Pyzo via either "python3 -m pyzo" or
"python3 path/to/pyzo".

In the first case it simply imports pyzo. In the latter case, that import
will generally fail, in which case the parent directory is added to sys.path
and the import is tried again. Then "pyzo.start()" is called.
"""
try:
    import leo.core.leoGlobals as leo_g
    leo_g.pr('pyzo.__main__.py')
except Exception:
    leo_g.pr('FAIL: import leo_g')
    leo_g = None
import os
import sys

# Imports that are maybe not used in Pyzo, but are/can be in the tools.
# Import them now, so they are available in the frozen app.
if 0: # EKR:change
    import shutil  # noqa
    assert shutil # EKR.

# EKR:change. We *are* running a script.
# Add parent directory to sys.path and try again.
thisDir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.split(thisDir)[0])
try:
    import pyzo
except ImportError:
    raise ImportError('Could not import leo/external/pyzo.')

### Old code
    # if hasattr(sys, 'frozen') and sys.frozen:
        # app_dir = os.path.dirname(os.path.abspath(sys.executable))
        # # Enable loading from source
        # sys.path.insert(0, os.path.join(app_dir, 'source'))
        # sys.path.insert(0, os.path.join(app_dir, 'source/more'))
        # # Import
        # import pyzo
    # else:
        # # Try importing
        # try:
            # import pyzo
        # except ImportError:
            # # Very probably run as a script, either the package or the __main__
            # # directly. Add parent directory to sys.path and try again.
            # thisDir = os.path.abspath(os.path.dirname(__file__))
            # sys.path.insert(0, os.path.split(thisDir)[0])
            # try:
                # import pyzo
            # except ImportError:
                # raise ImportError('Could not import Pyzo in either way.')
def main():
    pyzo.start()
        # Defined in pyzo.__init__.
print('__main__', __name__)
if __name__ == '__main__':
    main()
