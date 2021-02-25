
import threading
import time

from piweather.base.components import Component
from piweather.settings import SOUND_ENABLED


class Sound(Component):
    """
    This class uses VLC to play sounds one after another.
    It waits for the previous sound to finish, before a new one can be played.
    """
    lock = threading.Lock()  # lock for playing

    def __init__(self, settings):
        super().__init__(settings=settings)
        self._sound_thread: threading.Thread = None

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
            with self.lock:  # wait for previous sound to end
                player.play()
                time.sleep(2)  # wait for starting
                while player.is_playing():
                    time.sleep(1)
        except Exception as error:
            self._logger.warning("Sound: Cannot play sound: %s", str(error))
