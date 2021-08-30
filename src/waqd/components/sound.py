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

import threading
import time

from waqd.base.components import Component
from waqd.settings import SOUND_ENABLED


class Sound(Component):
    """
    This class uses VLC to play sounds one after another.
    It waits for the previous sound to finish, before a new one can be played.
    """
    lock = threading.Lock()  # lock for playing

    def __init__(self, settings):
        super().__init__(settings=settings)
        self._sound_thread: threading.Thread

    def play(self, audio_file):
        if not self._settings.get(SOUND_ENABLED):
            return
        Process = threading.Thread
        self._sound_thread = Process(
            name="Sound", target=self._call_vlc, args=(audio_file,)
        )
        self._sound_thread.start()

    def _call_vlc(self, audio_file):
        """
        """
        try:
            # import needs libs and can can crash appplication
            import vlc  # pylint: disable=import-outside-toplevel
            player = vlc.MediaPlayer(str(audio_file))
            vlc.libvlc_audio_set_volume(player, 140) # make it louder for passive loudspeakers
            with self.lock:  # wait for previous sound to end
                player.play()
                time.sleep(2)  # wait for starting
                while player.is_playing():
                    time.sleep(1)
        except Exception as error:
            self._logger.warning("Sound: Cannot play sound: %s", str(error))
