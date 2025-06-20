import os
import tempfile
from pathlib import Path
import shutil
from waqd import __version__
from installer import common, setup_system
from installer.common import assure_file_does_not_exist


def test_add_to_autostart(base_fixture):
    auto_update_file = base_fixture.testdata_path / "auto_updater" / "autostart.txt"
    temp_autostart_file = Path(tempfile.gettempdir()) / "tmp.txt"

    shutil.copy(str(auto_update_file), str(temp_autostart_file))
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


def test_get_version():
    assert common.get_waqd_version(common.installer_root_dir) == __version__


def test_get_waqd_bin_name():
    assert common.get_waqd_bin_name() == ("waqd." + __version__)


def test_get_waqd_bin_dir_name():
    assert common.get_waqd_bindir_name() == ("waqd." + __version__).replace(".", "-")


def test_get_install_path():
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


def test_register_autostart(base_fixture):
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


def test_clean_desktop(base_fixture):
    # no error should happen if file does not exist
    desktop_path = Path(tempfile.gettempdir()) / "tmp.conf"
    assure_file_does_not_exist(desktop_path)
    setup_system.clean_lxde_desktop(desktop_path)
    assert desktop_path.exists()

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


def test_unattended_upgrades_config(base_fixture):
    auto_updates_path = Path(tempfile.gettempdir()) / "tmp.conf"
    unattended_updates_path: Path = base_fixture.testdata_path / "auto_updater" / "50unattended-upgrades"

    with open(auto_updates_path, "w") as fd:
        fd.write('APT::Periodic::Update-Package-Lists "0";\n')
        fd.write('APT::Periodic::Unattended-Upgrade "1";')
    setup_system.configure_unnattended_updates(auto_updates_path)
    content = auto_updates_path.read_text()
    assert 'Update-Package-Lists "1"' in content
    assert 'Unattended-Upgrade "1"' in content

    content = unattended_updates_path.read_text()
    assert 'MinimalSteps "true"' in content
    assert 'AutoFixInterruptedDpkg "true"' in content
    assert 'Remove-Unused-Dependencies "false"' in content

# TODO
# def testEnableHwAccess
#     setup_system.

# def testHideMouseCursor

# def testCustomizeSplashScreen

# def testSetupSupportedLocales

# def testSetWallpaper
