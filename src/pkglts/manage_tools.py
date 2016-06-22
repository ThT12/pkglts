""" Specific helper function for manage script
"""

from importlib import import_module
import logging
from os import mkdir
from os.path import basename, exists, splitext
from os.path import join as pj

from .data_access import get, get_data_dir, ls
from .config_managment import ConfigSection, installed_options
from .install_env.load_front_end import get_install_front_end
from .local import init_namespace_dir
from .option_tools import get_user_permission
from .templating import render


logger = logging.getLogger(__name__)

tpl_src_name = "{" + "{ base.pkgname }" + "}"

non_bin_ext = ("", ".bat", ".cfg", ".in", ".ini", ".no", ".py", ".rst", ".sh",
               ".txt", ".yml")


def ensure_installed_packages(requirements, msg, env):
    """Ensure all packages in requirements are installed.

    If not, ask user permission to install them.

    Args:
        requirements (list of str): list of package names to install
                                   if needed
        msg (str): error message to print
        env (jinja2.Environment): current working environment

    Returns:
        (bool): whether all required packages are installed or not
    """
    ife = get_install_front_end(env.globals["_pkglts"].install_front_end)
    to_install = set(requirements) - set(ife.installed_packages())
    if len(to_install) > 0:
        print(msg)
        logger.warning("missing packages: " + ", ".join(to_install))
        for name in to_install:
            ife.install(name)
            logger.info("install %s", name)

    return True


def check_option_parameters(name, env):
    """Check that the parameters associated to an option are valid.

    Try to import Check function in option dir.

    Args:
        name (str): option name
        env (jinja2.Environment): current working environment
    """
    try:
        opt_cfg = import_module("pkglts.option.%s.config" % name)
        try:
            return opt_cfg.check(env)
        except AttributeError:
            return []
    except ImportError:
        return []


def update_opt(name, env):
    """Update an option of this package.

    Notes: If the option does not exists yet, add it first.
           See the list of available option online

    Args:
        name (str): name of option to add
        env (jinja2.Environment): current working environment
    """
    logger.info("update option %s", name)

    # test existence of option
    try:
        opt_require = import_module("pkglts.option.%s.require" % name)
        opt_cfg = import_module("pkglts.option.%s.config" % name)
    except ImportError:
        raise KeyError("option '%s' does not exists" % name)

    # find other option requirements in repository
    for option_name in opt_require.option:
        if option_name not in installed_options(env):
            print("need to install option '%s' first" % option_name)
            if (env.globals["_pkglts"].auto_install or
                    get_user_permission("install")):
                env = update_opt(option_name, env)
            else:
                return env

    # find extra package requirements for setup
    msg = "this option requires some packages to setup"
    if not ensure_installed_packages(opt_require.setup, msg, env):
        print("option installation stopped")
        return env

    # find parameters required by option config
    try:
        params = opt_cfg.parameters
    except AttributeError:
        params = []

    option_cfg = ConfigSection()
    prev_cfg = env.globals.get(name, {})
    for key, default in params:
        option_cfg.add_param(key, getattr(prev_cfg, key, default))

    # write new pkg_info file
    env.globals[name] = option_cfg

    try:  # TODO: proper developer doc to expose this feature
        opt_cfg.after(env)
    except AttributeError:
        pass

    # find extra package requirements for dvlpt
    msg = "this option requires additional packages for developers"
    ensure_installed_packages(opt_require.dvlpt, msg, env)

    return env


def render_dir(src_dir, tgt_dir, env, overwrite_file):
    """Walk all files in src_dir and create/update them on tgt_dir

    Args:
        src_dir (str): path to reference files
        tgt_dir (str): path to target where files will be written
        env (jinja2.Environment): current working environment
        overwrite_file (dict of str:bool): whether or not to overwrite some
                             files

    Returns:
        (list of str): list of all error files
    """
    error_files = []

    for src_name, is_dir in ls(src_dir):
        print "cur", src_name
        src_pth = src_dir + "/" + src_name
        tgt_name = env.from_string(src_name).render()
        if tgt_name.endswith(".tpl"):
            tgt_name = tgt_name[:-4]

        tgt_pth = tgt_dir + "/" + tgt_name
        # handle namespace
        if (is_dir and basename(src_dir) == 'src' and
                    src_name == tpl_src_name):
            namespace = env.globals['base'].namespace
            if namespace is not None:
                ns_pth = tgt_dir + "/" + namespace
                if not exists(ns_pth):
                    mkdir(ns_pth)

                init_namespace_dir(ns_pth)
                tgt_pth = ns_pth + "/" + tgt_name

        if is_dir:
            if tgt_name not in ("", "_") and not exists(tgt_pth):
                mkdir(tgt_pth)

            ef = render_dir(src_pth, tgt_pth, env, overwrite_file)
            error_files.extend(ef)
        else:
            fname, ext = splitext(tgt_name)
            if ext in non_bin_ext:
                render(env, pj(get_data_dir(), src_pth), tgt_pth)
            else:  # binary file
                if exists(tgt_pth):
                    print "overwrite?"
                else:
                    content = get(src_pth, 'rb')
                    with open(tgt_pth, 'wb') as fw:
                        fw.write(content)

    return error_files
