from pkglts.config_management import create_env
from pkglts.option.landscape.config import require


def test_require():
    cfg = dict(landscape={})
    env = create_env(cfg)

    assert len(require('option', env)) == 2
    assert len(require('setup', env)) == 0
    assert len(require('install', env)) == 0
    assert len(require('dvlpt', env)) == 0
