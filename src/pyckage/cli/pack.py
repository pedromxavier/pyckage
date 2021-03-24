import os
import json
import argparse

from ..pyckage import Pyckage, _PYCKAGE_DATA as package_data
from ..pyckagelib.error import PyckageError

def pack(args: argparse.Namespace):
    try:
        ## Validate args
        pyckage = Pyckage.from_args(args)

        

        if os.path.exists(pyckage_path):
            ## TODO: update pyckage
            # pyckage = Pyckage.load(args)
            Pyckage.exit(0, 'pyckage already built.')
        else:
            if args.package is None:
                args.package = os.path.basename(os.path.normpath(path))

            package = Pyckage.validate.package(args.package)

            config = package_data.get_config()

            pyckage = Pyckage(
                package=package,
                author=config.author,
                email=config.email,
                user=config.user,
                path=path
                )

            ## Create directories and files
            tree = pyckage.package_tree(args)
            tree.grow()

        with open(pyckage_path, 'w') as file:
            pyckage.pathlog.append([pyckage.FILE, '.pyckage'])
            json.dump(pyckage.json, file)

    except:
        pyckage.rollback()
        raise