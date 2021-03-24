import os
import json
import argparse

from ..pyckage import Pyckage, _PYCKAGE_DATA as package_data
from ..pyckagelib.error import PyckageError

def pack(args: argparse.Namespace):
    try:
        pyckage = Pyckage.from_args(args)
        print(pyckage)
    except:
        pass
