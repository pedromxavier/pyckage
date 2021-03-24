""" Pyckage - A Python package utility.
"""
import argparse
from ..pyckage import Pyckage
from ..pyckagelib import PyckageExit, PyckageError

## Commands
from .pack import pack
from .clear import clear
from .config import config

class PyckageParser(argparse.ArgumentParser):
    pass

def main():
    kwargs = {
        'prog': 'pyckage',
        'description': __doc__,
    }

    parser = PyckageParser(**kwargs)
    subparsers = parser.add_subparsers()

    ## pack
    pack_parser = subparsers.add_parser('pack')
    pack_parser.add_argument('path', type=str, nargs='?', help='packaging path.')
    pack_parser.add_argument('-p', '--package', type=str, action='store', help='project name.')
    pack_parser.add_argument('-d', '--data', action='store_true', help='whether to store external data.')
    pack_parser.add_argument('-s', '--script', action='store_true', help='whether to deploy cli script.')
    pack_parser.add_argument('-g', '--github', action='store_true', help='whether to add github info.')
    pack_parser.set_defaults(func=pack)

    ## clear
    clear_parser = subparsers.add_parser('clear')
    clear_parser.add_argument('path', type=str, nargs='?', help='packaging path.')
    clear_parser.set_defaults(func=clear)

    ## config
    subparser = subparsers.add_parser('config')
    subparser.add_argument('-a', '--author', help='sets default author name.')
    subparser.add_argument('-e', '--email', help='sets default email address.')
    subparser.add_argument('-u', '--user', help='sets default username (github).')
    subparser.set_defaults(func=config)
    

    ## run
    args = parser.parse_args()
    try:
        args.func(args)
    except PyckageExit as exit_:
        exit(exit_.code)
    else:
        exit(0)


if __name__ == '__main__':
    main()