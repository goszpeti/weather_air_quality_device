

from abc import ABC, abstractmethod
from os import PathLike
from threading import Lock, Thread
import time

from waqd.base.component_reg import Component, ComponentRegistry
from waqd.base.file_logger import Logger


class SoundInterface(ABC, Component):
    """
    Abstract Class to implement sound access.
    """

    @abstractmethod
    def play(self, audio_file: PathLike):
        """ Play an audio file (non-blocking) """
        raise NotImplementedError


class SoundVLC(SoundInterface):
    """
    This class uses VLC to play sounds one after another.
    It waits for the previous sound to finish, before a new one can be played.
    """
    lock = Lock()  # lock for playing

    def __init__(self, components: ComponentRegistry, enabled=True):
        super().__init__(components, enabled=enabled)
        self._sound_thread = Thread()
        self._ready = True

    def play(self, audio_file: PathLike):
        if self._disabled:
            return
        self._sound_thread = Thread(
            name="Sound", target=self._call_vlc, args=(audio_file,))
        self._sound_thread.start()

    def _call_vlc(self, audio_file: PathLike):
        """
        """
        try:
            # import needs libs and can can crash appplication
            import vlc  # pylint: disable=import-outside-toplevel
            player: vlc.MediaPlayer = vlc.MediaPlayer(str(audio_file)) # type: ignore
            assert player is not None
            vlc.libvlc_audio_set_volume(player, 120)  # make it louder for passive loudspeake
            if self._comps and self._comps.energy_saver.night_mode_active:  # lower volume at night
                player.audio_set_volume(50)
            with self.lock:  # wait for previous sound to end
                player.play()
                time.sleep(2)  # wait for starting
                while player.is_playing():
                    time.sleep(1)
        except Exception as error:
            self._logger.warning("Sound: Cannot play sound: %s", str(error))


class SoundQt(SoundInterface):
    """
    This class uses Qt to play sounds one after another.
    It waits for the previous sound to finish, before a new one can be played.
    """
    lock = Lock()  # lock for playing

    def __init__(self, components: ComponentRegistry, enabled=True):
        super().__init__(components, enabled=enabled)
        self._sound_thread = Thread()
        from PyQt5.QtMultimedia import QMediaPlayer
        self._player = QMediaPlayer()
        self._player.mediaStatusChanged.connect(self._on_player_status_changed)
        self._ready = True

    def _on_player_status_changed(self, id):
        Logger().debug(f"Media: {id}")
        # release lock, to play the next file
        if (
            id == self._player.MediaStatus.EndOfMedia
            or id == self._player.MediaStatus.InvalidMedia
        ):
            if self.lock.locked():
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
        from PyQt5.QtMultimedia import QMediaContent
        from PyQt5 import QtCore
        try:
            self.lock.acquire(True)  # wait for previous sound to end
            self._player.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(str(audio_file))))
            self._player.setVolume(140)
            if self._comps and self._comps.energy_saver.night_mode_active:  # lower volume at night
                self._player.setVolume(50)
            self._player.play()
        except Exception as error:
            self._logger.warning("Sound: Cannot play sound: %s", str(error))
        self.lock.release()
