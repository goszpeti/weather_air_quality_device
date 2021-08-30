import os
import tarfile

from urllib import request
from distutils.file_util import copy_file

import pytest
from waqd import config
from waqd import __version__ as VERSION
from waqd.settings import UPDATER_KEY, Settings, UPDATER_USER_BETA_CHANNEL, AUTO_UPDATER_ENABLED
from waqd.components.updater import OnlineUpdater
from waqd.base.components import ComponentRegistry

RASPI_BASE_IMAGE = "raspi/raspbian_py:1"
WAQD_IMAGE = "raspi/waqd_install:1"

def testCheckShouldUpdate(base_fixture):
    import waqd.components.updater as updater
    settings = Settings(ini_folder=base_fixture.base_path / "src")
    settings.set(AUTO_UPDATER_ENABLED, True)
    settings.set(UPDATER_USER_BETA_CHANNEL, True)
    comps = ComponentRegistry(settings)

    online_updater = OnlineUpdater(comps, settings)
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
    settings.set(UPDATER_USER_BETA_CHANNEL, False)
    assert not online_updater._check_should_update("1.0.0b19")
    assert not online_updater._check_should_update("1.1.0b2")

    # Beta Version
    # Beta Version to Main Version
    updater.WAQD_VERSION = "1.1.0b1"
    assert not online_updater._check_should_update("1.0.0")
    assert online_updater._check_should_update("1.2.0")

    # Beta Version to Beta Version
    settings.set(UPDATER_USER_BETA_CHANNEL, True)
    assert not online_updater._check_should_update("1.1.0b0")
    assert online_updater._check_should_update("1.1.0b2")
    settings.set(UPDATER_USER_BETA_CHANNEL, False)
    assert not online_updater._check_should_update("1.1.0b2")

    # Beta Version to Alpha Version
    # negative test, not enabled
    assert not online_updater._check_should_update("1.1.0a2")
    # enable - higher version should work
    updater.config.DEBUG_LEVEL = 1
    settings.set(UPDATER_USER_BETA_CHANNEL, True)
    assert online_updater._check_should_update("1.1.0a2")
    # lower or equal should not
    assert not online_updater._check_should_update("1.1.0a1")
    assert not online_updater._check_should_update("1.1.0a0")

    # Alpha Version
    updater.WAQD_VERSION = "1.1.0a1"
    settings.set(UPDATER_USER_BETA_CHANNEL, True)
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


@pytest.mark.updater
def testCreateBaseImageInDocker(base_fixture):
    if config.DEBUG_LEVEL == 0:
        pytest.skip("unsupported configuration")
    # --memory="xMB
    docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {RASPI_BASE_IMAGE} -f ./test/testdata/auto_updater/dockerfile_base"
    ret = os.system(docker_base_cmd)
    assert ret == 0

@pytest.mark.updater
def testInstallInDocker(base_fixture):
    if config.DEBUG_LEVEL == 0:
        pytest.skip("unsupported configuration")
    docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {WAQD_IMAGE} -f ./test/testdata/auto_updater/dockerfile_install"
    ret = os.system(docker_base_cmd)
    assert ret == 0
    # DEBUG: run manually
    # /home/pi/waqd-dev/script/installer/start_installer.sh > system_install.log
    # export DISPLAY=192.168.1.103:0
    # source /usr/local/waqd/1.5.0b0/bin/activate


@pytest.mark.updater
def testUpdaterLegacy(base_fixture):
    if config.DEBUG_LEVEL == 0:
        pytest.skip("unsupported configuration")
    settings = Settings(ini_folder=base_fixture.base_path / "src")
    key = settings.get(UPDATER_KEY)
    from github import Github
    github = Github(key)
    repository = github.get_user().get_repo(config.GITHUB_REPO_NAME)

    # download as tar because direct support
    legacy_install_dir = base_fixture.base_path / "v1.4.4"
    os.makedirs(legacy_install_dir, exist_ok=True)
    if not os.listdir(legacy_install_dir):
        [update_file, _] = request.urlretrieve(repository.get_archive_link("tarball", "v1.4.4"))
        tar = tarfile.open(update_file)
        tar.extractall(path=legacy_install_dir)

    # get install subfolder
    sub_dirs = os.listdir(legacy_install_dir)[0]
    legacy_install_dir = legacy_install_dir / sub_dirs

    # copy local config.ini with updater key
    copy_file(base_fixture.base_path / "src" / "config.ini", legacy_install_dir / "src")

    # enable debug mode
    with open(legacy_install_dir / "src" / "piweather" / "config.py", "r+") as fd:
        entries = fd.readlines()
        fd.seek(0)
        fd.truncate()
        new_entries = []
        # remove lxpanel --profile entry and legacy entries
        for entry in entries:
            if "DEBUG_LEVEL =" in entry:
                new_entries.append("DEBUG_LEVEL = 1\n")
            else:
                new_entries.append(entry)
        fd.writelines(new_entries)

    # src/components/updater.py   if self._runtime_system.is_target_system: -> if true;
    with open(legacy_install_dir / "src" / "piweather" / "components" / "updater.py", "r+") as fd:
        entries = fd.readlines()
        fd.seek(0)
        fd.truncate()
        new_entries = []
        for entry in entries:
            if "if self._runtime_system.is_target_system" in entry:
                new_entries.append("        if True:\n")
            else:
                new_entries.append(entry)
        fd.writelines(new_entries)

    docker_base_cmd = f"docker build {str(legacy_install_dir)} -t raspi/waqd_install_legacy:1" + \
        " -f ./test/testdata/auto_updater/dockerfile_install_legacy"
    ret = os.system(docker_base_cmd)
    assert ret == 0


def testUpdateSelf(base_fixture):
    if config.DEBUG_LEVEL == 0:
        pytest.skip("unsupported configuration")
    
    # enable beta update mode?
   
    # copy local config.ini with updater key
    #copy_file(base_fixture.base_path / "src" / "config.ini", legacy_install_dir / "src")
    from installer import common
    install_path = common.get_waqd_install_path(common.installer_root_dir)
    
    docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {WAQD_IMAGE} --build-arg WAQD_INSTALL_ROOT={install_path.as_posix()}" + \
        " -f ./test/testdata/auto_updater/dockerfile_update"
    ret = os.system(docker_base_cmd)
    assert ret == 0


