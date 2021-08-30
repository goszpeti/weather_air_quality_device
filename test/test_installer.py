import os
import tempfile
from distutils.file_util import copy_file
from pathlib import Path

from waqd import __version__


def testAddToAutostart(base_fixture):
    from installer import common
    auto_update_file = base_fixture.testdata_path / "auto_updater" / "autostart.txt"
    temp_autostart_file = Path(tempfile.gettempdir()) / "tmp.txt"

    copy_file(str(auto_update_file), str(temp_autostart_file))
    common.add_to_autostart("xscreensaver -no-splash", ["waqd"], temp_autostart_file)
    with open(temp_autostart_file) as ft:
        read = ft.readlines()
    assert read[0] == "@lxpanel --profile LXDE-pi\n"
    assert read[1] == "@pcmanfm --desktop --profile LXDE-pi\n"
    assert read[2] == "@xscreensaver -no-splash\n"
    
    # 2nd run - don't change anything
    common.add_to_autostart("xscreensaver -no-splash", [], temp_autostart_file)
    with open(temp_autostart_file) as ft:
        read = ft.readlines()
    assert read[0] == "@lxpanel --profile LXDE-pi\n"
    assert read[1] == "@pcmanfm --desktop --profile LXDE-pi\n"
    assert read[2] == "@xscreensaver -no-splash\n"
    assert len(read) == 3

def testGetVersion():
    from installer import common
    assert common.get_waqd_version(common.installer_root_dir) == __version__


def testGetWaqdBinName():
    from installer import common
    assert common.get_waqd_bin_name() == "waqd." + __version__


def testGetInstallPath():
    # reimport with env var set
    user = os.getenv("USER", "")
    if not user:  # for windows
        user = "user"
        os.environ["SUDO_USER"] = user

    from installer import common
    install_path = common.get_waqd_install_path(common.installer_root_dir)
    version_suffix = __version__
    assert install_path == Path(f"/home/{user}/.local/pipx/venvs/waqd.{version_suffix}")


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
