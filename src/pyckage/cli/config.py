import pathlib
import argparse

from ..pyckage import Pyckage, PyckageValidate, _PYCKAGE_DATA as package_data

def config(args: argparse.Namespace):
    if args.global_:
        config_global(args)
    else:
        config_local(args)

def config_local(args: argparse.Namespace):
    """"""
    if args.path is None:
        path = pathlib.Path.cwd().absolute()
    else:
        path = pathlib.Path(args.path).absolute()

    if not Pyckage.has_pyckage(path):
        print(f"No Pyckage installed at `{args.path}`.")
        return
    
    pyckage = Pyckage.load(path)

def config_global(args: argparse.Namespace):
    """"""
    config = {
        'author': PyckageValidate.author(args.author, null=True),
        'email': PyckageValidate.email(args.email, null=True),
        'user': PyckageValidate.user(args.user, null=True)
    }

    updates = {k: v for k, v in config.items() if v is not None}

    config = package_data.get_config()

    if not updates:
        for k, v in config.items():
            print(f"{k} = {v}")
    else:
        for k, v in updates.items():
            config[k] = v

        package_data.set_config(config)