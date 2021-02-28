import os
import re
import sys
import site
import json
import argparse
import configparser
from contextlib import contextmanager

__version__ = '0.1.0'

class PyckageError(Exception):
    pass

class PyckageExit(Exception):

    def __init__(self, code: int=0, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.code = code

class PyckageFormatter(dict):

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return f'{{{key}}}' if value is None else value

    def __missing__(self, key):
        return f'{{{key}}}'

class PyckageParser(argparse.ArgumentParser):
    pass

class Pyckage(object):
    """
    """

    DIR = sys.intern('DIR')
    FILE = sys.intern('FILE')

    _PACKAGE_DATA = 'pyckage_data'

    _DEFAULT_TREE = {
        'src': lambda p, args: {p.package : ['__init__.py']},
        'bin': lambda p, args: args.script,
        'docs': True,
        'data': lambda p, args: args.data,
        'setup.py': 'setup.py',
        'setup.cfg': 'setup.cfg'
    }

    _SETUP = {
        'PY_MIN': f"{sys.version_info.major}.{sys.version_info.minor}",
        'PY_MAX': f"{sys.version_info.major + 1}"
    }

    def __init__(self, *,
            package: str=None,
            version: str=None,
            author: str=None,
            path: str=None,
            done: list=None,
            description: str=None,
            **kwargs):
        self.package = package
        self.version = version
        self.author = author
        self.path = os.path.abspath(path)
        self.done = [('FILE', os.path.join(self.path, '.pyckage'))] if done is None else done
        self.description = description
        
        ## private
        self.__settings = None

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
    def from_json(cls, mapping: dict):
        return cls(**mapping)

    @property
    def json(self):
        return {
            'description': self.description,
            'version': __version__,
            'package': self.package,
            'author': self.author,
            'path': self.path,
            'done': self.done
        }

    @property
    def settings(self):
        if self.__settings is None:
            self.__settings = self.get_config()
        return self.__settings

    @property
    def setup_kwargs(self):
        return {**self.json, **self.settings, **self._SETUP}

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
            pyckage_path = os.path.join(path, '.pyckage')
            if os.path.exists(pyckage_path):
                ## TODO: update pyckage
                # pyckage = cls.load(args)
                cls.exit(0, 'pyckage already built.')
            else:
                if args.package is None:
                    args.package = os.path.basename(os.path.normpath(path))

                package = cls.validate.package(args.package)
                pyckage = cls(
                    package=package,
                    path=path
                    )

                ## Create directories and files
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

    def setup_cfg(self, args: argparse.Namespace):
        cfg_files = ['setup-plain.cfg']

        if args.data:
            cfg_files.append('setup-data.cfg')
        
        if args.script:
            cfg_files.append('setup-script.cfg')
        
        if args.github:
            cfg_files.append('setup-github.cfg')

        parser = configparser.ConfigParser()
        parser.read([self.get_path(self._PACKAGE_DATA, fname) for fname in cfg_files])

        setup_path = os.path.join(self.path, 'setup.cfg')

        with open(setup_path, 'w') as file:
            parser.write(file)

        with open(setup_path, 'r') as file:
            source = file.read()

        with open(setup_path, 'w') as file:
            file.write(source.format_map(PyckageFormatter(self.setup_kwargs)))

    def template(self, from_: str, to_: str, args: argparse.Namespace):
        if from_ == 'setup.cfg':
            self.setup_cfg(args)
        else:
            with open(self.get_path(self._PACKAGE_DATA, from_), 'r') as r_file:
                with open(to_, 'w') as w_file:
                    w_file.write(r_file.read())

    def grow_tree(self, path:str, tree: dict, args: argparse.Namespace):
        if type(tree) is not dict:
            raise TypeError('Argument ``tree`` must be dict.')
        else:
            for k, v in tree.items():
                if callable(v): v = v(self, args)

                new_path = os.path.join(path, k)
                
                if v is None: ## File
                    self.done.append([self.FILE, new_path])
                    self.touch(new_path)
                elif v is True: ## Empty dir
                    self.done.append((self.DIR, new_path))
                    os.mkdir(new_path)
                elif v is False: ## Skip
                    continue
                elif type(v) is dict: ## Go deeper
                    self.done.append((self.DIR, new_path))
                    os.mkdir(new_path)
                    with self.chdir(new_path):
                        self.grow_tree(new_path, v, args)
                elif type(v) is list: ## Go deeper - All files alias
                    self.done.append((self.DIR, new_path))
                    os.mkdir(new_path)
                    with self.chdir(new_path):
                        self.grow_tree(new_path, {k: None for k in v}, args)
                elif type(v) is str: ## load template
                    self.done.append([self.FILE, new_path])
                    self.template(from_=v, to_=new_path, args=args)
                else:
                    raise TypeError("Invalid type in tree.")

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
    def get_config(cls) -> dict:
        path = cls.get_path(cls._PACKAGE_DATA, '.pyckage-config')
        with open(path, 'r') as file:
            return json.load(file)
    
    @classmethod
    def set_config(cls, settings: dict):
        path = cls.get_path(cls._PACKAGE_DATA, '.pyckage-config')
        with open(path, 'w') as file:
            json.dump(settings, file)  

    @classmethod
    def config(cls, args: argparse.Namespace):
        fields = {
            'author': cls.validate.author(args.author, null=True),
            'email': cls.validate.email(args.email, null=True),
            'user': cls.validate.user(args.user, null=True)
        }

        updates = {k: v for k, v in fields.items() if v is not None}

        settings = cls.get_config()

        if not updates:
            for k, v in settings.items():
                print(f"{k} = {v}")
        else:
            for k, v in updates.items():
                settings[k] = v

            cls.set_config(settings)

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
        cls.pack_parser.add_argument('path', type=str, nargs='?', help='packaging path.')
        cls.pack_parser.add_argument('-p', '--package', type=str, action='store', help='project name.')
        cls.pack_parser.add_argument('-d', '--data', action='store_true', help='whether to store external data.')
        cls.pack_parser.add_argument('-s', '--script', action='store_true', help='whether to deploy cli script.')
        cls.pack_parser.add_argument('-g', '--github', action='store_true', help='whether to add github info.')
        cls.pack_parser.set_defaults(func=cls.pack)

        ## clear
        cls.clear_parser = subparsers.add_parser('clear')
        cls.clear_parser.add_argument('path', type=str, nargs='?', help='packaging path.')
        cls.clear_parser.set_defaults(func=cls.clear)

        ## config
        cls.config_parser = subparsers.add_parser('config')
        cls.config_parser.add_argument('-a', '--author', help='sets default author name.')
        cls.config_parser.add_argument('-e', '--email', help='sets default email address.')
        cls.config_parser.add_argument('-u', '--user', help='sets default username (github).')
        cls.config_parser.set_defaults(func=cls.config)

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

        RE_AUTHOR = None
        RE_EMAIL = re.compile(r'^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$')
        RE_VERSION = re.compile(r'^(0|[1-9]\d*)(\.(0|[1-9]\d*))(\.(0|[1-9]\d*))?$')
        RE_PACKAGE = re.compile(r'^[a-zA-Z][a-zA-Z\_\-]+$')

        @classmethod
        def _regex(cls, regex: re.Pattern, s: str, field: str="", null: bool=False):
            if s is None and null:
                return s
            elif type(s) is not str or regex.match(s) is None:
                raise ValueError(f"Invalid {field}: {s}")
            else:
                return s

        @classmethod
        def author(cls, author: str, null:bool=False):
            return author

        @classmethod
        def user(cls, user: str, null:bool=False):
            return user

        @classmethod
        def email(cls, email: str, null:bool=False):
            return cls._regex(cls.RE_EMAIL, email, 'email', null=null)

        @classmethod
        def version(cls, version: str, null:bool=False) -> str:
            return cls._regex(cls.RE_VERSION, version, 'version', null=null)

        @classmethod
        def package(cls, package: str, null:bool=False) -> str:
            return cls._regex(cls.RE_PACKAGE, package, 'package name', null=null)

        @classmethod
        def path(cls, path: {str, None}, null:bool=False) -> str:
            if path is None:
                return os.path.abspath(os.getcwd())
            elif type(path) is str:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Path `{path}` not found.")
                else:
                    return os.path.abspath(path)
            else:
                raise TypeError(f"Invalid path type {type(path)}")

def main(*args, **kwargs):
    return Pyckage.cli(*args, **kwargs)

if __name__ == '__main__':
    main()