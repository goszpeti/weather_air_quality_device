import os
import tarfile
import platform
from distutils.file_util import copy_file
from docker.client import DockerClient
import pytest
import waqd
from waqd import __version__ as VERSION
from waqd.settings import Settings, UPDATER_USER_BETA_CHANNEL, AUTO_UPDATER_ENABLED
#guestfish --ro -a /home/peter/2022-01-28-raspios-bullseye-arm64.img -m /dev/sda2:/ tar-out / - | docker import - waqd
# docker build . -t goszpeti/raspi-base:latest -f ./test/testdata/auto_updater/dockerfile_base
# docker run --privileged --name rpi -v /sys/fs/cgroup:/sys/fs/cgroup:ro -td goszpeti/waqd systemd

USERNAME = "pi"
RASPI_BASE_IMAGE = "goszpeti/raspi-base:latest"
WAQD_IMAGE = "goszpeti/waqd:latest"
#RUNAS_CMD = "runuser -u " + USERNAME

def testInstallInDockerWithoutGUI(base_fixture):
    """ Start an installation with the installer running without the updater ui. """
    client = DockerClient()

    docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {WAQD_IMAGE} -f ./test/testdata/auto_updater/dockerfile_install"
    if platform.system() == "Linux":
        docker_base_cmd = docker_base_cmd + " | tee install.log"
    ret = os.system(docker_base_cmd)
    assert ret == 0
    cont = client.containers.run(
        WAQD_IMAGE, name="waqd-install-test", detach=True, auto_remove=True, privileged=True,
        volumes=["/sys/fs/cgroup:/sys/fs/cgroup:ro"], command="systemd")
    # RUN bash -lic "./home/pi/waqd-dev/script/installer/exec_install.sh && waqd_install"
    # check if pipx installed
    # cont.logs()
    res = cont.attach()
   
    res = cont.exec_run("./waqd-dev/script/installer/exec_install.sh", user="pi")
    res = cont.exec_run("python3 -m pipx --version", user="pi")
    assert res.exit_code == 0
    # check if pyqt-5 is installed
    res = cont.exec_run("qtchooser -l", user="pi")
    assert b"qt5" in res.output
    # check if waqd is installed
    res = cont.exec_run("/home/pi/.local/bin/waqd.{VERSION} --version")
    assert VERSION in res.output.decode("utf-8")
    # get waqd-start executable

    # check if it was set for autostart

    # check system setup
    # autostart
    #arch = cont.get_archive("/home/pi/.config/lxsession/LXDE-pi/autostart")

    # ... TODO
    #cont.attach()
    # TODO finally
    cont.stop()

    # TODO at the end
    client.images.prune()

# @pytest.mark.updater
# def testUpdaterLegacy(base_fixture):
#     if waqd.DEBUG_LEVEL == 0:
#         pytest.skip("unsupported configuration")
#     settings = Settings(ini_folder=base_fixture.base_path / "src")
#     from github import Github
#     github = Github()
#     repository = github.get_user().get_repo(waqd.GITHUB_REPO_NAME)

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

#     # copy local waqd.ini with updater key
#     copy_file(base_fixture.base_path / "src" / "waqd.ini", legacy_install_dir / "src")

#     # enable debug mode
#     with open(legacy_install_dir / "src" / "piweather" / "waqd.py", "r+") as fd:
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
#     if waqd.DEBUG_LEVEL == 0:
#         pytest.skip("unsupported configuration")

#     # enable beta update mode?

#     # copy local waqd.ini with updater key
#     #copy_file(base_fixture.base_path / "src" / "waqd.ini", legacy_install_dir / "src")
#     from installer import common
#     install_path = common.get_waqd_install_path(common.installer_root_dir)

#     docker_base_cmd = f"docker build {str(base_fixture.base_path)} -t {WAQD_IMAGE} --build-arg WAQD_INSTALL_ROOT={install_path.as_posix()}" + \
#         " -f ./test/testdata/auto_updater/dockerfile_update"
#     ret = os.system(docker_base_cmd)
#     assert ret == 0
