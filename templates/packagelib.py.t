import os
import sys
import site

PACKAGE_DATA = '{package_data}'

def get_data_path(fname: str, package_data: str=PACKAGE_DATA) -> str:
    """
    """
    sys_path = os.path.abspath(os.path.join(sys.prefix, package_data, fname))
    usr_path = os.path.abspath(os.path.join(site.USER_BASE, package_data, fname))
    if not os.path.exists(sys_path):
        if not os.path.exists(usr_path):
            raise FileNotFoundError(f"File {{fname}} not installed in {{package_data}}.")
        else:
            return usr_path
    else:
        return sys_path

def open_data(fname: str, mode: str='r', *args: tuple, **kwargs: dict):
    """
    """
    return open(os.path.join(get_data_path(''), fname), mode=mode, *args, **kwargs)

