import os
import re
import sys
import site
import json
import argparse
from contextlib import contextmanager

__version__ = '0.1.0'

class PyckageError(Exception):
    pass

class PyckageExit(Exception):

    def __init__(self, code: int=0, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.code = code

class PyckageParser(argparse.ArgumentParser):
    pass

class Pyckage(object):
    """
    """

    DIR = sys.intern('DIR')
    FILE = sys.intern('FILE')
    

    _DEFAULT_TREE = {
        'src': ['__init__.py'],
        'bin': lambda args: args.script,
        'docs': True,
        'data': lambda args: args.data,
        'setup.py': 'setup.py',
        'setup.cfg': 'setup.cfg'
    }

    def __init__(self, 
            package: str=None,
            version: str=None,
            author: str=None,
            path: str=None,
            done: list=None,
            *args, **kwargs):
        self.package = package
        self.version = version
        self.author = author
        self.path = os.path.abspath(path)
        self.done = [('FILE', os.path.join(self.path, '.pyckage'))] if done is None else done
    
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
                raise FileNotFoundError(f"File {fname} not installed in {package_data}.")
            else:
                return usr_path
        else:
            return sys_path

    @staticmethod
    def touch(path: str):
        with open(path, 'a'):
            pass

    @classmethod
    def from_json(cls, json: dict):
        return cls(**json)

    @property
    def json(self):
        return {
            'version': __version__,
            'package': self.package,
            'author': self.author,
            'path': self.path,
            'done': self.done
        }

    @classmethod
    def ask(cls, question: str, requestion: str=None, validate: callable=None):
        requestion = question if requestion is None else requestion

        answer = input(question)
        if validate is not None:
            while True:
                try:
                    answer = validate(answer)
                    break
                except cls.validate.Invalid:
                    answer = input(requestion)
                    continue
        return answer
        

    @classmethod
    def pack(cls, args: argparse.Namespace):
        cls.done = [] ## Rollback/Uninstall purposes
        
        try:
            ## Validate args
            path = cls.validate.path(args.path)
            package = cls.validate.package(args.package)

            pyckage_path = os.path.join(path, '.pyckage')

            if os.path.exists(pyckage_path):
                ## TODO: update pyckage
                # pyckage = cls.load(args)
                cls.exit(0, 'pyckage already built.')
            else:
                pyckage = cls(package=package, path=path)

                ## Create directories
                pyckage.grow_tree(path, cls._DEFAULT_TREE, args)

            with open(pyckage_path, 'w') as file:
                json.dump(pyckage.json, file)

        except PyckageError:
            pyckage.rollback()
            raise
        except:
            pyckage.rollback()
            raise

    def rollback(self):
        while self.done:
            kind, path = self.done.pop()
            if kind == 'FILE':
                if os.path.exists(path):
                    print(f"delete {path}")
                    os.remove(path)
            elif kind == 'DIR':
                if os.path.exists(path):
                    print(f"delete {path}")
                    os.rmdir(path)
            else:
                raise ValueError('Serious trouble.')

    def template(self, from_: str, to_: str):
        with open(self.get_path('pyckage_data', from_), 'r') as r_file:
            with open(to_, 'w') as w_file:
                for line in r_file:
                    w_file.write(line)

    def grow_tree(self, path:str, tree: dict, args: argparse.Namespace):
        if type(tree) is not dict:
            raise TypeError('Argument ``tree`` must be dict.')
        else:
            for k, v in tree.items():
                if callable(v): v = v(args)

                new_path = os.path.join(path, k)
                
                if v is None: ## File
                    self.touch(new_path)
                    self.done.append([self.FILE, new_path])
                elif v is True: ## Empty dir
                    os.mkdir(new_path)
                    self.done.append((self.DIR, new_path))
                elif v is False: ## Skip
                    continue
                elif type(v) is dict: ## Go deeper
                    os.mkdir(new_path)
                    self.done.append((self.DIR, new_path))
                    with self.chdir(new_path):
                        self.grow_tree(new_path, v, args)
                elif type(v) is list: ## Go deeper - All files alias
                    os.mkdir(new_path)
                    self.done.append((self.DIR, new_path))
                    with self.chdir(new_path):
                        self.grow_tree(new_path, {k: None for k in v}, args)
                elif type(v) is str: ## load template
                    self.template(from_=v, to_=new_path)
                    self.done.append([self.FILE, new_path])
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
    def clear(cls, args: argparse.Namespace):
        pyckage: cls = cls.load(args)
        pyckage.rollback()

    @classmethod
    def load(cls, args: argparse.Namespace):
        path = cls.validate.path(args.path)
        
        pyckage_path = os.path.join(path, '.pyckage')
        
        if os.path.exists(pyckage_path):
            with open(pyckage_path, 'r') as file:
                return cls.from_json(json.load(file))
        else:
            cls.exit(1, f'No pyckage defined at `{path}`.')

    @classmethod
    def exit(cls, code: int=0, msg: str=""):
        raise PyckageExit(code, msg)

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
        cls.pack_parser.add_argument('package', type=str, help='project name.')
        cls.pack_parser.add_argument('path', type=str, nargs='?', help='packaging path.')
        cls.pack_parser.add_argument('-d', '--data', action='store_true', help='whether to store external data.')
        cls.pack_parser.add_argument('-s', '--script', action='store_true', help='whether to deploy cli script.')
        cls.pack_parser.set_defaults(func=cls.pack)

        ## build
        cls.build_parser = subparsers.add_parser('clear')
        cls.build_parser.add_argument('path', type=str, nargs='?', help='packaging path.')
        cls.build_parser.set_defaults(func=cls.clear)

        ## run
        args = cls.parser.parse_args()
        try:
            args.func(args)
        except PyckageExit as exit_:
            exit(exit_.code)
        else:
            exit(0)

    class validate:

        class Invalid(Exception):
            pass

        RE_VERSION = re.compile(r'^(0|[1-9]\d*)(\.(0|[1-9]\d*))(\.(0|[1-9]\d*))?$')
        RE_PACKAGE = re.compile(r'^[a-zA-Z][a-zA-Z\_\-]+$')

        @classmethod
        def version(cls, version: str) -> str:
            if type(version) is not str or cls.RE_VERSION.match(version) is None:
                raise ValueError(f"Invalid version: {version}")
            else:
                return version

        @classmethod
        def package(cls, package: str) -> str:
            if type(package) is not str or cls.RE_PACKAGE.match(package) is None:
                raise ValueError(f"Invalid packge name: {package}")
            else:
                return package

        @classmethod
        def path(cls, path: {str, None}) -> str:
            if path is None:
                return os.path.abspath(os.getcwd())
            elif type(path) is str:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Path `{path}` not found.")
                else:
                    return os.path.abspath(path)
            else:
                raise TypeError(f"Invalid path type {type(path)}")

main = Pyckage.cli

if __name__ == '__main__':
    main()