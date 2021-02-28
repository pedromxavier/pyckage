import os
import re
import sys
import site
import json
import argparse
from contextlib import contextmanager

__version__ = '0.1.0'

class PyckageParser(argparse.ArgumentParser):
    ...

class Pyckage(object):
    """
    """

    _DEFAULT_TREE = {
        'src': ['__init__.py'],
        'docs': [],
        'data': lambda args: args.data,
        'setup.py': None,
        'setup.cfg': None
    }

    def __init__(self, package: str, version: str, author: str, *args, **kwargs):
        self.package = package
        self.version = version
        self.author = author
    
    @staticmethod
    @contextmanager
    def chdir(path: str):
        cwd_path: str = os.path.abspath(os.getcwd())
        try:
            os.chdir(path)
            yield path
        finally:
            os.chdir(cwd_path)

    @staticmethod
    def get_path(package_data: str, fname: str) -> str:
        sys_path = os.path.abspath(os.path.join(sys.prefix, package_data, fname))
        usr_path = os.path.abspath(os.path.join(site.USER_BASE, package_data, fname))
        if not os.path.exists(sys_path):
            if not os.path.exists(usr_path):
                raise FileNotFoundError("File {fname} not installed in {package_data}.")
            else:
                return usr_path
        else:
            return sys_path

    @staticmethod
    def touch(path: str):
        with open(path, 'a'):
            pass

    @classmethod
    def pack(cls, args: argparse.Namespace):
        path = os.path.abspath(args.path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"``{path}`` not found.")

        with open('.pyckage', 'w') as file:
            json.dump({
                'version': __version__,
                'package': args.name,
                'path': path
            }, file)

        ## Create directories
        cls.grow_tree(path, cls._DEFAULT_TREE, args)

    @classmethod
    def grow_tree(cls, path:str, tree: dict, args: argparse.Namespace):
        if type(tree) is not dict:
            raise TypeError('Argument ``tree`` must be dict.')
        else:
            for k, v in tree.items():
                if callable(v): v = v(args)
                    
                if v is None: ## file
                    cls.touch(os.path.join(path, k))
                elif v is True:
                    os.mkdir(os.path.join(path, k))
                elif v is False:
                    continue
                elif type(v) is dict:
                    new_path = os.path.join(path, k)
                    os.mkdir(new_path)
                    with cls.chdir(new_path):
                        cls.grow_tree(new_path, v, args)
                elif type(v) is list:
                    new_path = os.path.join(path, k)
                    os.mkdir(new_path)
                    with cls.chdir(new_path):
                        cls.grow_tree(new_path, {k: None for k in v}, args)
                else:
                    raise TypeError("Invalid type in tree.")

    @classmethod
    def pack_subdirs(cls, args: argparse.Namespace):
        subdirs = ['src', 'docs']
        if args.data:
            subdirs.append('data')
        return subdirs

    @classmethod
    def pack_files(cls, args: argparse.Namespace):
        files = ['setup.py', 'setup.cfg']
        return files

    @classmethod
    def build(cls, args: argparse.Namespace):
        ...

    @classmethod
    def cli(cls):
        """Command-line interface
        """
        kwargs = {
            'prog': 'pyckage',
            'description':cls. __doc__,
        }

        cls.parser = PyckageParser(**kwargs)
        subparsers = cls.parser.add_subparsers()

        ## pack
        cls.pack_parser = subparsers.add_parser('pack')
        cls.pack_parser.add_argument('name', type=str, help='project name.')
        cls.pack_parser.add_argument('path', type=str, nargs='?', help='root path.')
        cls.pack_parser.set_defaults(func=cls.pack)

        ## build
        cls.build_parser = subparsers.add_parser('build')
        cls.build_parser.set_defaults(func=cls.build)

        ## run
        args = cls.parser.parse_args()
        args.func(args)

def main():
    return Pyckage.cli()

if __name__ == '__main__':
    main()