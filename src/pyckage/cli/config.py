import argparse

from ..pyckage import Pyckage, PyckageValidate, _PYCKAGE_DATA as package_data

def config(args: argparse.Namespace):
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