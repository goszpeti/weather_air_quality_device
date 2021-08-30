import argparse
from installer import install, setup_system, common


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--install",
                        action='store_true')
    group.add_argument("--setup_system",
                        action='store_true')
    group.add_argument("--set_wallpaper",
                       action='store_true')
    args = parser.parse_args()

    if args.install:
        install.do_install()
    elif args.setup_system:
        setup_system.do_setup()
    elif args.set_wallpaper: # need to handle this separately
        setup_system.set_wallpaper(common.get_waqd_install_path())
