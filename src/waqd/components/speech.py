
import os
import time
from threading import Thread

from gtts import gTTS
import waqd
from waqd.base.component_reg import Component, ComponentRegistry
from waqd.base.network import Network
from waqd.base.translation import Translation, LANGS_MAP
from waqd.settings import LANG_ENGLISH


class TextToSpeach(Component):
    """
    This class uses Google TTS and VLC player for TTS functionality.
    It waits for the previous sound to finish, before a new one can be played.
    A little delay is normal, since TTS is computed in the cloud and the file sent back.
    """

    def __init__(self, components: ComponentRegistry, lang="en"):
        super().__init__(components)
        self._lang = lang
        self._tts_thread = Thread()
        self._save_dir = waqd.user_config_dir / "tts"
        # ensure dir exists
        os.makedirs(self._save_dir, exist_ok=True)
        self._ready = True

    def get_tts_string(self, key: str, lang="en") -> str:
        return Translation().get_localized_string("tts_dict", key, lang)

    def say_internal(self, key="", format_args=[]):
        """
        Internal wrapper function for TTS.
        Key corresponds to an entry in the tts_dict.json.
        Language is determined from settings.
        """
        text = self.get_tts_string(key, self._lang)
        self.say(text.format(*format_args), self._lang)

    def say(self, text="", lang=LANG_ENGLISH, filename=""):
        """
        User function for TTS.
        :param lang: switches between official GTTS languages.
        """
        if self._comps and self._comps.sound.is_disabled:
            return

        self._tts_thread = Thread(
            name="google_TTS", target=self._call_tts, args=(text, lang, filename,)
        )
        self._tts_thread.start()

    def wait_for_tts(self):
        """ Bock until speech is finished """
        if self._tts_thread:
            while self._tts_thread.is_alive():
                time.sleep(1)

    def _call_tts(self, text, lang, filename):
        """
        Download tts as mp3 and play with VLC. Blocks execution. To be used in a separate thread.
        """
        # remap, if given as setting
        if lang in LANGS_MAP:
            lang = LANGS_MAP.get(lang, "")
        try:
            if not filename:
                # remove most likeable pitfalls. Is not comprehensive!
                normalized_text = text.replace(' ', '_').replace(
                '.', '_').replace('/', '').replace(',', '_').strip()
                filename = normalized_text[0:30]
            audio_file = self._save_dir / f"{filename}_{lang}.mp3"
            # only download, if file does not exist
            if filename or not audio_file.is_file():
                Network().wait_for_internet()
                gtts = gTTS(text, lang=lang)
                gtts.save(audio_file)
            if self._comps: # Play sound
                self._comps.sound.play(audio_file)
            self._logger.debug("Speech: Finished: %s", text)
        except Exception as error:
            self._logger.warning("Speech: Cannot use text to speech engine.: %s", str(error))
