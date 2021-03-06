from pkglts.dependency import Dependency
from pkglts.option_tools import available_options


def requirements(cfg, requirement_name):
    """Check all requirements for installed options.

    Args:
        cfg (Config):  current package configuration
        requirement_name (str): type of requirement 'install', 'dvlpt'

    Returns:
        (list of str): list of required packages names
    """
    reqs = {}
    for name in cfg.installed_options():
        try:
            opt = available_options[name]
            for dep in opt.require(requirement_name, cfg):
                reqs[dep.name] = dep
        except KeyError:
            raise KeyError("option '%s' does not exists" % name)

    return [reqs[name] for name in sorted(reqs)]


def pkg_url(cfg):
    try:
        url = cfg['base']['url']
        if url is not None:
            return url
    except KeyError:
        pass

    try:
        url = cfg['github']['url']
        if url is not None:
            return url
    except KeyError:
        pass

    try:
        url = cfg['pypi']['url']
        if url is not None:
            return url
    except KeyError:
        pass

    try:
        url = cfg['readthedocs']['url']
        if url is not None:
            return url
    except KeyError:
        pass

    return ""


def environment_extensions(cfg):
    """Add more functionality to an environment.

    Args:
        cfg (Config):  current package configuration

    Returns:
        dict of str: any
    """
    req_install = requirements(cfg, 'install')
    for dep in cfg['pysetup']['require']:
        req_install.append(Dependency(**dep))

    req_dvlpt = requirements(cfg, 'dvlpt')

    def req(name):
        if name == 'install':
            return req_install
        elif name == 'dvlpt':
            return req_dvlpt
        else:
            raise UserWarning("WTF")

    return {"pkg_url": pkg_url(cfg),
            "requirements": req}
