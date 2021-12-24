
import pytest
from waqd import config
from waqd import __version__ as VERSION
from waqd.settings import Settings, UPDATER_USER_BETA_CHANNEL, AUTO_UPDATER_ENABLED
from waqd.components.updater import OnlineUpdater
from waqd.base.component_reg import ComponentRegistry

RASPI_BASE_IMAGE = "raspi/raspbian_py:1"
WAQD_IMAGE = "raspi/waqd_install:1"

def testRepoIsReachable(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    comps = ComponentRegistry(settings)
    online_updater = OnlineUpdater(comps, enabled=True, use_beta_channel=True)
    online_updater._connect_to_repository()
    assert online_updater._repository # only check if object exists


def testCheckShouldUpdate(base_fixture):
    import waqd.components.updater as updater # import the module here, so we can access the loaded global var of WAQD version
    settings = Settings(base_fixture.testdata_path / "integration")
    comps = ComponentRegistry(settings)

    online_updater = OnlineUpdater(comps, enabled=True, use_beta_channel=True)
    # Main versions to Main versions
    updater.WAQD_VERSION = "1.1.0"
    # same version -  no update
    assert not online_updater._check_should_update("v1.1.0")  # use v to see if it is cut
    # lesser version - no update
    assert not online_updater._check_should_update("1.0.0")
    # higher version
    assert online_updater._check_should_update("1.2.0")

    # Main Version
    # Main version to Beta version
    # beta flag enabled
    # lesser version - no update
    assert not online_updater._check_should_update("1.0.0b19")
    # same version - but Beta -> must be older
    assert not online_updater._check_should_update("1.1.0b2")
    # higher version
    assert online_updater._check_should_update("1.2.0b0")

    # beta flag disabled - no update
    online_updater._use_beta_channel = False
    assert not online_updater._check_should_update("1.0.0b19")
    assert not online_updater._check_should_update("1.1.0b2")

    # Beta Version
    # Beta Version to Main Version
    updater.WAQD_VERSION = "1.1.0b1"
    assert not online_updater._check_should_update("1.0.0")
    assert online_updater._check_should_update("1.2.0")

    # Beta Version to Beta Version
    online_updater._use_beta_channel = True
    assert not online_updater._check_should_update("1.1.0b0")
    assert online_updater._check_should_update("1.1.0b2")
    online_updater._use_beta_channel = False
    assert not online_updater._check_should_update("1.1.0b2")

    # Beta Version to Alpha Version
    # negative test, not enabled
    assert not online_updater._check_should_update("1.1.0a2")
    # enable - higher version should work
    updater.config.DEBUG_LEVEL = 1
    online_updater._use_beta_channel = True
    assert online_updater._check_should_update("1.1.0a2")
    # lower or equal should not
    assert not online_updater._check_should_update("1.1.0a1")
    assert not online_updater._check_should_update("1.1.0a0")

    # Alpha Version
    updater.WAQD_VERSION = "1.1.0a1"
    online_updater._use_beta_channel = True
    updater.config.DEBUG_LEVEL = 1
    # to alpha
    assert online_updater._check_should_update("1.1.0a2")
    assert not online_updater._check_should_update("1.1.0a0")
    assert not online_updater._check_should_update("1.1.0a1")
    # to beta
    assert online_updater._check_should_update("1.1.0b2")
    assert online_updater._check_should_update("1.1.0b1")
    # TODO currently will always update to beta
    assert online_updater._check_should_update("1.1.0b0")
    # to main
    assert online_updater._check_should_update("1.1.0")
    assert online_updater._check_should_update("1.2.0")
    assert not online_updater._check_should_update("1.0.0")
    # disabled debug level - only update to beta or main
    updater.config.DEBUG_LEVEL = 0
    # TODO: updates from alpha to alpha
    assert online_updater._check_should_update("1.1.0a2")
    assert online_updater._check_should_update("1.1.0b1")
    assert online_updater._check_should_update("1.1.0")
