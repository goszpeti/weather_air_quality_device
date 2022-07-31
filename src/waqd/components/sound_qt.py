#
# Copyright (c) 2019-2021 Péter Gosztolya & Contributors.
#
# This file is part of WAQD
# (see https://github.com/goszpeti/WeatherAirQualityDevice).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from os import PathLike
from threading import Lock, Thread
from waqd.base.logger import Logger
from waqd.base.component_reg import Component, ComponentRegistry
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5 import QtCore

class Sound(Component):
    """
    This class uses Qt to play sounds one after another.
    It waits for the previous sound to finish, before a new one can be played.
    """
    lock = Lock()  # lock for playing

    def __init__(self, components: ComponentRegistry, enabled=True):
        super().__init__(components, enabled=enabled)
        self._sound_thread = Thread()
        self._player = QMediaPlayer()
        self._player.mediaStatusChanged.connect(self.on_player_status_changed)
        
    def on_player_status_changed(self, id):
        Logger().debug(f"Media: {id}")
        # release lock, to play the next file
        if id == self._player.EndOfMedia or id == self._player.InvalidMedia:
            self.lock.release()

    def play(self, audio_file: PathLike):
        if self._disabled:
            return
        self._sound_thread = Thread(
            name="Sound", target=self._call_qt, args=(audio_file,))
        self._sound_thread.start()

    def _call_qt(self, audio_file: PathLike):
        """
        """
        try:
            self.lock.acquire(True)  # wait for previous sound to end
            self._player.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(str(audio_file))))
            self._player.setVolume(140)
            if self._comps and self._comps.energy_saver.night_mode_active:  # lower volume at night
                self._player.setVolume(50)
            self._player.play()
        except Exception as error:
            self._logger.warning("Sound: Cannot play sound: %s", str(error))
