import json
from os.path import exists
from os.path import join as pj
import pytest

from pkglts.config_management import (Config, current_pkg_cfg_version,
                                      default_cfg, get_pkg_config,
                                      write_pkg_config)

from .small_tools import ensure_created, rmdir


@pytest.fixture()
def tmp_dir():
    pth = "toto_mg_cfg"
    ensure_created(pth)
    ensure_created(pj(pth, ".pkglts"))

    yield pth

    if exists(pth):
        rmdir(pth)


def test_create_env():
    cfg = Config(default_cfg)
    assert len(tuple(cfg.installed_options())) == 0

    pkg_cfg = dict(default_cfg)
    pkg_cfg['base'] = dict(a=1, b=2)
    cfg = Config(pkg_cfg)
    assert len(tuple(cfg.installed_options())) == 1
    assert cfg['base']['a'] == 1
    assert cfg['base']['b'] == 2


def test_create_env_render_templates():
    pkg_cfg = dict(default_cfg)
    pkg_cfg['base'] = dict(a="a", b="b")
    pkg_cfg['tpl'] = dict(tpl1="{{ base.a }}",
                          tpl2="{{ base.b }} and {{ tpl.tpl1 }}")

    cfg = Config(pkg_cfg)
    assert cfg['tpl']['tpl1'] == "a"
    assert cfg['tpl']['tpl2'] == "b and a"


def test_create_env_raise_error_if_unable_to_fully_render_templates():
    pkg_cfg = dict(default_cfg)
    pkg_cfg['base'] = dict(a="{{ base.b }}", b="{{ base.a }}")

    with pytest.raises(UserWarning):
        Config(pkg_cfg)


def test_pkg_env_raise_error_if_option_not_defined():
    pkg_cfg = dict(default_cfg)
    pkg_cfg['babou'] = dict(a="a", b="b")

    with pytest.raises(KeyError):
        Config(pkg_cfg).load_extra()


def test_pkg_env_loads_specific_handlers_from_options():
    pkg_cfg = dict(default_cfg)
    pkg_cfg['base'] = dict(pkgname="toto", namespace="nm",
                           url=None, authors=[("moi", "moi@aussi")])

    cfg = Config(pkg_cfg)
    cfg.load_extra()
    assert hasattr(cfg._env.globals['base'], "pkg_full_name")


def test_get_pkg_config_read_cfg(tmp_dir):
    pkg_cfg = dict(default_cfg)
    pkg_cfg['base'] = dict(pkgname="toto", namespace="nm",
                           url=None, authors=[("moi", "moi@aussi")])
    json.dump(pkg_cfg, open(pj(tmp_dir, ".pkglts/pkg_cfg.json"), 'w'))

    cfg = get_pkg_config(tmp_dir)
    assert 'base' in cfg


def test_get_pkg_config_handle_versions(tmp_dir):
    pkg_cfg = dict(default_cfg)
    pkg_cfg["_pkglts"]["version"] = 0
    json.dump(pkg_cfg, open(pj(tmp_dir, ".pkglts/pkg_cfg.json"), 'w'))

    cfg = get_pkg_config(tmp_dir)
    assert cfg["_pkglts"]['version'] == current_pkg_cfg_version


def test_pkg_cfg_read_write_maintains_templates(tmp_dir):
    pkg_cfg = dict(default_cfg)
    pkg_cfg['base'] = dict(pkgname="toto", namespace="nm",
                           url=None, authors=[("moi", "moi@aussi")])
    pkg_cfg['license'] = dict(name="CeCILL-C", organization="org",
                              project="{{ base.pkgname }}", year="2015")

    json.dump(pkg_cfg, open(pj(tmp_dir, ".pkglts/pkg_cfg.json"), 'w'))

    cfg = get_pkg_config(tmp_dir)
    assert cfg['license']['project'] == "toto"

    write_pkg_config(cfg, tmp_dir)
    pkg_cfg = json.load(open(pj(tmp_dir, ".pkglts/pkg_cfg.json")))
    pkg_cfg["base"]["pkgname"] = "tutu"

    json.dump(pkg_cfg, open(pj(tmp_dir, ".pkglts/pkg_cfg.json"), 'w'))

    cfg = get_pkg_config(tmp_dir)
    assert cfg['license']['project'] == "tutu"
