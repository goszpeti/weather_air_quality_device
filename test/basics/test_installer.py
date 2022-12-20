import os
import tempfile
from distutils.file_util import copy_file
from pathlib import Path

from waqd import __version__
from installer import common, setup_system


def testAddToAutostart(base_fixture):
    auto_update_file = base_fixture.testdata_path / "auto_updater" / "autostart.txt"
    temp_autostart_file = Path(tempfile.gettempdir()) / "tmp.txt"

    copy_file(str(auto_update_file), str(temp_autostart_file))
    setup_system.add_to_autostart(["xscreensaver -no-splash"], temp_autostart_file)
    setup_system.remove_from_autostart(["waqd"], temp_autostart_file)

    with open(temp_autostart_file) as ft:
        read = ft.readlines()
    assert read[0] == "@lxpanel --profile LXDE-pi\n"
    assert read[1] == "@pcmanfm --desktop --profile LXDE-pi\n"
    assert read[2] == "@xscreensaver -no-splash\n"
    
    # 2nd run - don't change anything
    setup_system.add_to_autostart(["xscreensaver -no-splash"], temp_autostart_file)
    with open(temp_autostart_file) as ft:
        read = ft.readlines()
    assert read[0] == "@lxpanel --profile LXDE-pi\n"
    assert read[1] == "@pcmanfm --desktop --profile LXDE-pi\n"
    assert read[2] == "@xscreensaver -no-splash\n"
    assert len(read) == 3

def testGetVersion():
    assert common.get_waqd_version(common.installer_root_dir) == __version__


def testGetWaqdBinName():
    assert common.get_waqd_bin_name() == ("waqd." + __version__)


def testGetWaqdBinDirName():
    assert common.get_waqd_bindir_name() == ("waqd." + __version__).replace(".", "-")


def testGetInstallPath():
    # reimport with env var set
    home = os.getenv("HOME", "")
    if not home:  # for windows
        home = "/home/pi"
        os.environ["HOME"] = home
    from importlib import reload
    from installer import common
    reload(common)
    install_path = common.get_waqd_install_path(common.installer_root_dir)
    version_suffix = __version__.replace(".", "-")
    assert install_path.as_posix() == Path(f"{home}/.local/pipx/venvs/waqd-{version_suffix}").as_posix()


def testRegisterAutostart(base_fixture):
    from installer.common import get_waqd_bin_name
    auto_update_file = base_fixture.testdata_path / "auto_updater" / "autostart.txt"
    os.environ["SUDO_USER"] = "user"
    from installer import install

    # redirect output to a temp dir
    tempdir = Path(tempfile.gettempdir())
    temp_autostart_file = tempdir / "tmp.txt"

    copy_file(str(auto_update_file), str(temp_autostart_file))
    install.register_waqd_autostart(bin_path=tempdir/"bin",
                                    autostart_file=temp_autostart_file)
    start_waqd_path = tempdir / "bin" / "waqd-start"
    with open(start_waqd_path) as ft:
        read = ft.read()
    assert get_waqd_bin_name() in read

    with open(temp_autostart_file) as ft:
        read = ft.readlines()

    assert read[0] == "@lxpanel --profile LXDE-pi\n"
    assert read[1] == "@pcmanfm --desktop --profile LXDE-pi\n"
    assert read[2] == "@" + str(start_waqd_path) + "\n"


def testCleanDesktop(base_fixture):
    # no error should happen if file does not exist
    desktop_path = Path(tempfile.gettempdir()) / "tmp.conf"
    # setup_system.clean_lxde_desktop(desktop_path)
    #assert desktop_path.exists()

    desktop_path = Path(tempfile.gettempdir()) / "tmp.conf"
    with open(desktop_path, "w") as fd:
        fd.write("[*]\n")
        fd.write("show_trash=1\n")
        fd.write("show_mounts=1\n")
        fd.write("[New]\n")
        fd.write("x=1\n")
    setup_system.clean_lxde_desktop(desktop_path)
    text = desktop_path.read_text()
    assert "show_trash=0" in text
    assert "show_mounts=0" in text


def testUnattendedUpgradesConfig(base_fixture):
    auto_updates_path = Path(tempfile.gettempdir()) / "tmp.conf"
    with open(auto_updates_path, "w") as fd:
        fd.write('APT::Periodic::Update-Package-Lists "0";\n')
        fd.write('APT::Periodic::Unattended-Upgrade "1";')
    setup_system.configure_unnattended_updates(auto_updates_path)
    content = auto_updates_path.read_text()
    assert 'Update-Package-Lists "1"' in content
    assert 'Unattended-Upgrade "1"' in content

# TODO
# def testEnableHwAccess
#     setup_system.

# def testHideMouseCursor

# def testCustomizeSplashScreen

# def testSetupSupportedLocales

# def testSetWallpaper
