#!/bin/python3
# This script is being run as admin!

import logging
import os
import sys
from distutils.file_util import copy_file
from pathlib import Path
from subprocess import check_output

from installer.common import (HOME, USER_CONFIG_PATH, add_line_to_file, assure_file_exists, installer_root_dir,
                              add_to_autostart, remove_from_autostart, remove_line_in_file, set_write_permissions, setup_logger)


def enable_hw_access():
    # TODO need to add dtoverlay=rpi-backlight to /boot/config.txt

    # enable non-sudo usage of rpi-backlight
    rules_dir = "/etc/udev/rules.d"
    rules_file = "backlight-permissions.rules"
    rules_path = Path(rules_dir) / rules_file
    assure_file_exists(rules_path, chown=False)
    enable_text = 'SUBSYSTEM=="backlight",RUN+="/bin/chmod 666 /sys/class/backlight/%k/brightness' \
                ' /sys/class/backlight/%k/bl_power"'
    add_line_to_file([enable_text], rules_path, unique=True)

    # enable all needed hw accesses
    logging.info("Enable HW access (serial, i2c and spi)")
    os.system("raspi-config nonint do_serial 2")  # console off, serial on
    os.system("raspi-config nonint do_i2c 0")
    os.system("raspi-config nonint do_spi 0")
    # Allow port 80 to be accessed as non sudo
    os.system(f"setcap 'cap_net_bind_service=+ep' /usr/bin/python3.{str(sys.version_info.minor)}")


def disable_screensaver():
    logging.info("Check the screensaver")

    config_file = HOME / ".xscreensaver"
    switch_off_cmd = "mode: off\n"
    assure_file_exists(config_file, chown=False)
    logging.info("Disabling screen saver.")
    remove_line_in_file(["mode:"], config_file)
    add_line_to_file([switch_off_cmd], config_file)
    logging.info("Add the screensaver to autostart")
    add_to_autostart(["xscreensaver -no-splash"])


def hide_mouse_cursor():
    """ Modify xserver-command to append -nocursor """
    lightdm_config_file = Path("/usr/share/lightdm/lightdm.conf.d/01_debian.conf")
    assure_file_exists(lightdm_config_file, chown=False)
    logging.info("Hiding mouse cursor")
    remove_line_in_file(["xserver-command"], lightdm_config_file)
    add_line_to_file(["xserver-command=X -nocursor"], lightdm_config_file)


def customize_splash_screen():
    # copy splash screen to /usr/share/plymouth/themes/pix
    os.makedirs("/usr/share/plymouth/themes/pix", exist_ok=True)
    try:
        logging.info("Customizing splash screen")
        src_image = f"{str(installer_root_dir)}/src/waqd/assets/gui_base/splash_screen.png"
        copy_file(src_image,  "/usr/share/plymouth/themes/pix/splash.png")
        # remove rainbow screen
        os.system("raspi-config nonint set_config_var disable_splash 1 /boot/config.txt")
    except Exception as e:
        logging.error(str(e))


def setup_supported_locales():
    sup_locales = ["en_US.UTF8", "de_DE.UTF8", "hu_HU.UTF8"]
    # get locales:
    try:
        logging.info("Getting installed languages")
        installed_locales = check_output(["localectl", "list-locales"]).decode("utf-8")
    except Exception as e:
        logging.error(str(e))
        return
    # TODO check does not work!
    # set not installed locales in /etc/locale.gen
    locale_added = False
    for locale in sup_locales:
        if locale.lower() not in installed_locales.lower():
            os.system('echo "' + locale + ' UTF-8\n" | tee -a /etc/locale.gen')
            locale_added = True
    # generate them, if there is something to add
    if locale_added:
        try:
            logging.info("Generating locale")
            os.system("locale-gen")
        except Exception as e:
            logging.error(str(e))


def set_wallpaper(install_path: Path):
    # Can't be run as sudo, or as sudo -runuser. Needs desktop manager running.
    # set wallpaper - get image from install dir
    lib_paths = (install_path / "lib").iterdir() # TODO does not work anymore
    for lib_path in lib_paths:
        if "python" in lib_path.name:
            image = lib_path / "site-packages/waqd/assets/gui_base/pre_loading_screen.png"
            try:
                logging.info("Setting wallpaper..." + f'pcmanfm --set-wallpaper="{str(image)}"')
                os.system(f'pcmanfm --set-wallpaper="{str(image)}"')
            except Exception as e:
                logging.error(str(e))
            break


def clean_lxde_desktop(desktop_conf_path=Path(HOME / ".config/pcmanfm/LXDE-pi/desktop-items-0.conf")):
    # Can't be run as sudo, or as sudo -runuser. Needs desktop manager running.
    logging.info("Cleanup desktop icons...")
    assure_file_exists(desktop_conf_path)
    remove_line_in_file(["show_trash", "show_mounts"], desktop_conf_path)
    add_line_to_file(["show_trash=0", "show_mounts=0"], desktop_conf_path)

def do_setup():
    # System setup
    # Start only the desktop, but not the taskbar
    add_to_autostart(["pcmanfm --desktop --profile LXDE-pi"])
    remove_from_autostart(["lxpanel --profile"])


    # Cosmetic setup
    customize_splash_screen()
    hide_mouse_cursor()
    disable_screensaver()

    # Add languages
    setup_supported_locales()

    # Enable needed hardware access
    enable_hw_access()
