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
import json
import os
import time
from pathlib import Path
from threading import Thread, ThreadError

from gtts import gTTS
from waqd import config
from waqd.assets import get_asset_file
from waqd.base.components import Component, ComponentRegistry
from waqd.base.logger import Logger
from waqd.base.system import RuntimeSystem
from waqd.settings import LANG_ENGLISH, LANG_GERMAN, LANG_HUNGARIAN

# map settings to internal shortened lang names
LANGS_MAP = {
    LANG_ENGLISH: "en",
    LANG_GERMAN: "de",
    LANG_HUNGARIAN: "hu"
}


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
        self._save_dir = config.user_config_dir / "tts"
        # ensure dir exists
        os.makedirs(self._save_dir, exist_ok=True)

    def get_tts_string(self, key: str, lang="en") -> str:
        if lang in LANGS_MAP:
            lang = LANGS_MAP.get(lang)
        dict_file = get_asset_file("base", "tts_dict")
        # read filetoc.json
        with open(str(dict_file), encoding='utf-8') as f:
            tts_dict = json.load(f)

        # get filetype and filelist
        lang_dict = tts_dict.get(lang)
        if not lang_dict:
            self._logger.error(f"TTS: Cannot find language string for {lang}")
            return ""

        value = lang_dict.get(key)
        if not value:
            Logger().error("Cannot find resource id %s in catalog", key)
        return value

    def say_internal(self, key="", format_args=[]):
        """
        Internal wrapper function for TTS.
        Key corresponds to an entry in the tts_dict.json.
        Language is determined from settings.
        """
        lang = LANGS_MAP.get(self._lang, "en")
        text = self.get_tts_string(key, lang)
        self.say(text.format(*format_args), lang)

    def say(self, text="", lang="en"):
        """
        User function for TTS.
        :param lang: switches between official GTTS languages.
        """
        if self._comps and self._comps.sound.is_disabled:
            return

        self._tts_thread = Thread(
            name="google_TTS", target=self._call_tts, args=(text, lang,)
        )
        self._tts_thread.start()

    def wait_for_tts(self):
        """ Bock until speech is finished """
        if self._tts_thread:
            while self._tts_thread.is_alive():
                time.sleep(1)

    def _call_tts(self, text, lang):
        """
        Download tts as mp3 and play with VLC. Blocks execution. To be used in a separate thread.
        """
        # remap, if given as setting
        if lang in LANGS_MAP:
            lang = LANGS_MAP.get(lang)
        try:
            # remove most likeable pitfalls. Is not comprehensive!
            normalized_text = text.replace(' ', '_').replace(
                '.', '_').replace('/', '').replace(',', '_').strip()
            audio_file = self._save_dir / f"{normalized_text}_{lang}.mp3"
            # only download, if file does not exist
            if not audio_file.is_file():
                RuntimeSystem().wait_for_network()
                gtts = gTTS(text, lang=lang)
                gtts.save(audio_file)
            if self._comps:
                self._comps.sound.play(audio_file)
            self._logger.debug("Speech: Finished: %s", text)
        except Exception as error:
            self._logger.warning("Speech: Cannot use text to speech engine.: %s", str(error))
