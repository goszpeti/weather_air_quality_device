import os
import tarfile

from urllib import request
from distutils.file_util import copy_file

import pytest
from waqd import config
from waqd import __version__ as VERSION
from waqd.settings import Settings, UPDATER_USER_BETA_CHANNEL, AUTO_UPDATER_ENABLED
from waqd.components.updater import OnlineUpdater
from waqd.base.components import ComponentRegistry

RASPI_BASE_IMAGE = "raspi/raspbian_py:1"
WAQD_IMAGE = "raspi/waqd_install:1"

@pytest.mark.updater
def testCreateBaseImageInDocker(base_fixture):
    docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {WAQD_IMAGE} -f ./test/testdata/auto_updater/dockerfile_install"
    ret = os.system(docker_base_cmd)
    assert ret == 0
    # from docker.client import DockerClient
    # client = DockerClient()
    # client.images.build(path=str(base_fixture.base_path / "test/testdata/auto_updater"), dockerfile="dockerfile_base", tag=RASPI_BASE_IMAGE)


@pytest.mark.updater
def testInstallInDocker(base_fixture):
    from docker.client import DockerClient
    # client = DockerClient()
    # cont = client.containers.create(WAQD_IMAGE)
    # a = cont.attach()
    # cont.get_archive("home/pi/.config/lxsession/LXDE-pi/autostart")

    docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {WAQD_IMAGE} -f ./test/testdata/auto_updater/dockerfile_install"
    ret = os.system(docker_base_cmd)
    assert ret == 0
    # . /home/pi/waqd-dev/script/installer/exec_install.sh && waqd_install
    # DEBUG: run manually
    # /home/pi/waqd-dev/script/installer/start_installer.sh > system_install.log
    # export DISPLAY=192.168.1.103:0
    # source /usr/local/waqd/1.5.0b0/bin/activate

#RUN sudo /sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -screen 0 1920x1200x24 -ac +extension GLX  && ${COPY_PATH}/script/installer/start_installer.sh
# assertions
#RUN pipx --version
#RUN cat /home/pi/.local/pipx/venvs/waqd-1-6-0a6/lib/python3.7/site-packages/waqd/__init__.py


@pytest.mark.updater
def testUpdaterLegacy(base_fixture):
    if config.DEBUG_LEVEL == 0:
        pytest.skip("unsupported configuration")
    settings = Settings(ini_folder=base_fixture.base_path / "src")
    from github import Github
    github = Github()
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


