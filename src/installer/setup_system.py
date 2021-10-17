#!/bin/python3
# This script is being run as admin!

import logging
import os
from distutils.file_util import copy_file
from pathlib import Path
from subprocess import check_output

from installer.common import (HOME, USER_CONFIG_PATH, installer_root_dir,
                              add_to_autostart, set_write_premissions, setup_logger)


def enable_hw_access():
    # enable non-sudo usage of rpi-backlight
    rules_dir = "/etc/udev/rules.d"
    rules_file = "backlight-permissions.rules"
    os.system(f"sudo mkdir --parents {rules_dir}")
    if not os.path.exists(f"{rules_dir}/{rules_file}"):
        # create and append to file
        logging.info("Setting backlight permissions...")
        os.system(f"sudo touch {rules_dir}/{rules_file}")
        os.system(
            """echo 'SUBSYSTEM=="backlight",RUN+="/bin/chmod 666 /sys/class/backlight/%k/brightness """ +
            f"""/sys/class/backlight/%k/bl_power"' | tee -a {rules_dir}/{rules_file}""")

    # enable all needed hw accesses
    logging.info("Enable HW access (serial, i2c and spi)")
    os.system("raspi-config nonint do_serial 2")  # console off, serial on
    os.system("raspi-config nonint do_i2c 0")
    os.system("raspi-config nonint do_spi 0")


def disable_screensaver():
    logging.info("Check the screensaver")

    config_file = HOME / ".xscreensaver"
    switch_off_cmd = "mode: off\n"
    if not config_file.exists():
        logging.info("Cannot find .xscreensaver config file - creating it")
        with open(config_file, "w") as fd:
            fd.write(switch_off_cmd)
    else:
        with open(config_file, "r+") as fd:
            lines = fd.readlines()
            fd.seek(0)
            new_lines = []
            for line in lines:
                if line.startswith("mode:"):
                    line = switch_off_cmd
                    logging.info("Disabling screen saver.")
                new_lines.append(line)
            fd.writelines(new_lines)
    logging.info("Add the screensaver to autostart")
    add_to_autostart("xscreensaver -no-splash", [])


def hide_mouse_cursor():
    light_dm_config_file = Path("/usr/share/lightdm/lightdm.conf.d/01_debian.conf")
    if not light_dm_config_file.exists():
        logging.error("Cannot find lightdm config file to hide mouse.")
    # modify xserver-command to append -nocursor
    with open(light_dm_config_file, "r+") as fd:
        logging.info("Hiding mouse cursor")
        lines = fd.readlines()
        fd.seek(0)
        new_lines = []
        for line in lines:
            if not "xserver-command" in line:  # skip this
                new_lines.append(line)
        new_lines.append("xserver-command=X -nocursor\n")  # now add
        fd.writelines(new_lines)


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
    lib_paths = (install_path / "lib").iterdir()
    for lib_path in lib_paths:
        if "python" in lib_path.name:
            image = lib_path / "site-packages/waqd/assets/gui_base/pre_loading_screen.png"
            try:
                logging.info("Setting wallpaper...")
                os.system(f'pcmanfm --set-wallpaper="{image}"')
            except Exception as e:
                logging.error(str(e))
            break


def clean_lxde_desktop(desktop_conf_path=Path(HOME / ".config/pcmanfm/LXDE-pi/desktop-items-0.conf")):
    logging.info("Cleanup desktop icons...")
    if not desktop_conf_path.exists():
        return
    with open(desktop_conf_path, "r+") as fd:
        lines = fd.readlines()
        fd.seek(0)
        new_lines = []
        for line in lines:
            if "show_trash" in line:  # skip this
                line = "show_trash=0\n"
            elif "show_mounts" in line:
                line = "show_mounts=0\n"
            new_lines.append(line)
        fd.writelines(new_lines)


def do_setup():
    # System setup
    # Start only the desktop, but not the taskbar
    add_to_autostart("pcmanfm --desktop --profile LXDE-pi", ["lxpanel --profile"])

    # Cosmetic setup
    clean_lxde_desktop()
    customize_splash_screen()
    hide_mouse_cursor()
    disable_screensaver()

    # Add languages
    setup_supported_locales()

    # Enable needed hardware access
    enable_hw_access()
