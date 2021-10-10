import os
import tarfile
import platform
from urllib import request
from distutils.file_util import copy_file

from docker.client import DockerClient
import pytest
from waqd import config
from waqd import __version__ as VERSION
from waqd.settings import Settings, UPDATER_USER_BETA_CHANNEL, AUTO_UPDATER_ENABLED


RASPI_BASE_IMAGE = "goszpeti/waqd:1"
WAQD_IMAGE = "goszpeti/waqd_installed:1"

@pytest.mark.updater
def testInstallInDockerWithoutGUI(base_fixture):
    """ Start an installation with the installer running without the updater ui. """
    client = DockerClient()

    docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {WAQD_IMAGE} -f ./test/testdata/auto_updater/dockerfile_install"
    if platform.system() == "Linux":
        docker_base_cmd = docker_base_cmd + " | tee install.log"
    ret = os.system(docker_base_cmd)
    assert ret == 0

    cont = client.containers.create(WAQD_IMAGE, name="waqd-install-test", stdin_open=True, auto_remove=True)
    cont.start()
    # check if pipx installed
    res = cont.exec_run("python3 -m pipx --version", user="pi")
    assert res.exit_code == 0
    # qtchooser -l
    # check if waqd is installed
    #arch = cont.get_archive("/home/pi/.config/lxsession/LXDE-pi/autostart")
    # check system setup
    # autostart
    # ... TODO
    #cont.attach()

    cont.stop()
    # client.containers.prune()
    # TODO: cleanup stop running containers and delete them

    # . /home/pi/waqd-dev/script/installer/exec_install.sh && waqd_install
    # DEBUG: run manually
    # /home/pi/waqd-dev/script/installer/start_installer.sh > system_install.log
    # export DISPLAY=192.168.1.103:0
    # source /usr/local/waqd/1.5.0b0/bin/activate

#RUN sudo /sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -screen 0 1920x1200x24 -ac +extension GLX  && waqd.1.6.0b2
# assertions
#RUN cat /home/pi/.local/pipx/venvs/waqd-1-6-0a6/lib/python3.7/site-packages/waqd/__init__.py


# @pytest.mark.updater
# def testUpdaterLegacy(base_fixture):
#     if config.DEBUG_LEVEL == 0:
#         pytest.skip("unsupported configuration")
#     settings = Settings(ini_folder=base_fixture.base_path / "src")
#     from github import Github
#     github = Github()
#     repository = github.get_user().get_repo(config.GITHUB_REPO_NAME)

#     # download as tar because direct support
#     legacy_install_dir = base_fixture.base_path / "v1.4.4"
#     os.makedirs(legacy_install_dir, exist_ok=True)
#     if not os.listdir(legacy_install_dir):
#         [update_file, _] = request.urlretrieve(repository.get_archive_link("tarball", "v1.4.4"))
#         tar = tarfile.open(update_file)
#         tar.extractall(path=legacy_install_dir)

#     # get install subfolder
#     sub_dirs = os.listdir(legacy_install_dir)[0]
#     legacy_install_dir = legacy_install_dir / sub_dirs

#     # copy local config.ini with updater key
#     copy_file(base_fixture.base_path / "src" / "config.ini", legacy_install_dir / "src")

#     # enable debug mode
#     with open(legacy_install_dir / "src" / "piweather" / "config.py", "r+") as fd:
#         entries = fd.readlines()
#         fd.seek(0)
#         fd.truncate()
#         new_entries = []
#         # remove lxpanel --profile entry and legacy entries
#         for entry in entries:
#             if "DEBUG_LEVEL =" in entry:
#                 new_entries.append("DEBUG_LEVEL = 1\n")
#             else:
#                 new_entries.append(entry)
#         fd.writelines(new_entries)

#     # src/components/updater.py   if self._runtime_system.is_target_system: -> if true;
#     with open(legacy_install_dir / "src" / "piweather" / "components" / "updater.py", "r+") as fd:
#         entries = fd.readlines()
#         fd.seek(0)
#         fd.truncate()
#         new_entries = []
#         for entry in entries:
#             if "if self._runtime_system.is_target_system" in entry:
#                 new_entries.append("        if True:\n")
#             else:
#                 new_entries.append(entry)
#         fd.writelines(new_entries)

#     docker_base_cmd = f"docker build {str(legacy_install_dir)} -t raspi/waqd_install_legacy:1" + \
#         " -f ./test/testdata/auto_updater/dockerfile_install_legacy"
#     ret = os.system(docker_base_cmd)
#     assert ret == 0


# def testUpdateSelf(base_fixture):
#     if config.DEBUG_LEVEL == 0:
#         pytest.skip("unsupported configuration")
    
#     # enable beta update mode?
   
#     # copy local config.ini with updater key
#     #copy_file(base_fixture.base_path / "src" / "config.ini", legacy_install_dir / "src")
#     from installer import common
#     install_path = common.get_waqd_install_path(common.installer_root_dir)
    
#     docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {WAQD_IMAGE} --build-arg WAQD_INSTALL_ROOT={install_path.as_posix()}" + \
#         " -f ./test/testdata/auto_updater/dockerfile_update"
#     ret = os.system(docker_base_cmd)
#     assert ret == 0


