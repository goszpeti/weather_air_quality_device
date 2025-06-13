import argparse
import logging
import os
from . import install, setup_system, common


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--install",
                        action='store_true')
    group.add_argument("--setup_system",
                        action='store_true')
    group.add_argument("--set_wallpaper",
                       action='store_true')
    group.add_argument("--configure_languages", action="store_true")
    args = parser.parse_args()
    # ensure, that the config dir exists and is writable
    os.makedirs(str(common.USER_CONFIG_PATH), exist_ok=True)
    common.set_write_permissions(common.USER_CONFIG_PATH)
    log_file = common.USER_CONFIG_PATH / "waqd_install.log"
    common.set_write_permissions(log_file)
    common.setup_logger(log_file)

    if args.install:
        install.do_install()
    elif args.setup_system:
        setup_system.do_setup()
    elif args.set_wallpaper: # need to handle this separately
        setup_system.set_wallpaper(common.get_waqd_install_path())
        setup_system.clean_lxde_desktop()
    elif args.configure_languages:
        # Add languages
        setup_system.setup_supported_locales()
    else:
        logging.info("Nothing to do!")
