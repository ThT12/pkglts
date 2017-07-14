from glob import glob
from os import path

from pkglts.config_management import create_env
from pkglts.data_access import get_data_dir
from pkglts.option_tools import available_options, find_available_options

find_available_options()


def test_options_expose_parameters():
    # walk through all possible options defined by pkglts
    option_basedir = path.join(path.dirname(get_data_dir()), 'pkglts', 'option')
    for pth in glob("{}/*/".format(option_basedir)):
        option_name = path.basename(path.dirname(pth))
        if not option_name.startswith("_"):
            # check 'config' module exists for each option
            try:
                opt = available_options[option_name]
                assert len(opt.parameters) >= 0
            except KeyError:
                assert False


def test_require_correctly_defined():
    cfg = dict(base={}, test={'suite_name': 'pytest'})
    env = create_env(cfg)

    # walk through all possible options
    option_basedir = path.join(path.dirname(get_data_dir()), 'pkglts', 'option')
    for pth in glob("{}/*/".format(option_basedir)):
        option_name = path.basename(path.dirname(pth))
        if not option_name.startswith("_"):
            # check 'require' function exists for each option
            try:
                opt = available_options[option_name]
                assert len(opt.require('option', env)) >= 0
                assert len(opt.require('setup', env)) >= 0
                assert len(opt.require('install', env)) >= 0
                assert len(opt.require('dvlpt', env)) >= 0
            except ImportError:
                assert False
