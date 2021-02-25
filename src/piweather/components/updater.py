import os
import shutil
import urllib.request
from pathlib import Path
from time import sleep
from github import Github, Repository
from packaging import version

import piweather.config as config
from piweather import __version__ as PIWHEATER_VERSION
from piweather.base.components import ComponentRegistry, CyclicComponent
from piweather.settings import UPDATER_KEY, LANG


class OnlineUpdater(CyclicComponent):
    """
    Auto updater class, which checks for new releases on GitHub with an access token
    If a newer version is detected, it downloads it and calls "script/installer/start_installer.sh"
    This entry point should not be changed!
    """
    UPDATE_TIME = 600  # 10 minutes in seconds
    INIT_WAIT_TIME = 10  # don't start updating until the station is ready
    STOP_TIMEOUT = 2  # override because of long update time

    def __init__(self, components: ComponentRegistry, settings):
        super().__init__(components, settings)

        self._base_path = config.base_path  # save for multiprocessing
        self._repository: Repository = None

        if not self._settings.get(UPDATER_KEY):
            self._logger.warning("Updater: No updater key specified, function is disabled")
            self._disabled = True
            return

        self._new_version_dir = Path.home() / ".PiWeather_update"

        # delete downloaded version to clean up
        if self._new_version_dir.exists():
            shutil.rmtree(self._new_version_dir)

        self._start_update_loop(self._updater_sequence, self._updater_sequence)

    def _updater_sequence(self):
        """ Check, that runs continously and start the installation if a new version is available. """
        self._connect_to_repository(self._settings.get(UPDATER_KEY))
        [update_available, tag_name] = self._check_update()
        if update_available:
            self._install_update(tag_name)

    def _connect_to_repository(self, updater_key):
        """ Get Github repo object """
        github = Github(updater_key)
        self._repository = github.get_user().get_repo(config.GITHUB_REPO_NAME)

    def _check_update(self) -> [bool, str]:
        """ Check, if an update is found and return it's version. """
        logger = self._logger

        releases = self._repository.get_releases()
        if releases:
            latest_release = releases[0]

        latest_version = version.parse(latest_release.tag_name)

        if latest_version > version.parse(PIWHEATER_VERSION):
            # only install pre-releases on debug mode
            if (latest_release.prerelease or latest_release.draft) and config.DEBUG_LEVEL == 0:
                return [False, None]
            logger.info("Updater: Found newer version %s", latest_version)
            self._comps.tts.say_internal("new_version", [latest_version])
            return [True, latest_release.tag_name]

        logger.debug("Updater: No new update found")
        return [False, latest_release.tag_name]

    def _install_update(self, tag_name):
        """
        Start the installer at the defined entry point:
        script/installer/start_installer.sh
        """
        # TODO do a popup later with deferring option?

        # download as tar because direct support
        [update_file, _] = urllib.request.urlretrieve(
            self._repository.get_archive_link("tarball", tag_name))
        import tarfile  # pylint: disable=import-outside-toplevel
        tar = tarfile.open(update_file)
        tar.extractall(path=self._new_version_dir)

        # the repo will be in a randomly named dir, so we must scan for it
        update_dir = [f.path for f in os.scandir(self._new_version_dir) if f.is_dir()]
        if len(update_dir) != 1:
            self._logger.error("Updater: Multiple update repos found")
            return
        update_dir = Path(update_dir[0])

        # Wait for previous peach to finish berfore this app intance is killed
        self._comps.tts.wait_for_tts()

        # start updater script - location hardcoded
        if self._runtime_system.is_target_system:
            installer_script = update_dir / "script" / "installer" / "start_installer.sh"
            if installer_script.exists():
                try:
                    self._logger.info("Updater: Starting updater")
                    os.system("chmod +x " + str(installer_script))
                    # this kills this program
                    os.system(str(installer_script))
                except RuntimeError as error:
                    self._logger.error(
                        "Updater: Error while executing updater: \n%s", str(error))
