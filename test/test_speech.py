from waqd.components.speech import TextToSpeach
from waqd.settings import SOUND_ENABLED, Settings
from waqd.base.components import ComponentRegistry

import time


def testTTSParallel(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(SOUND_ENABLED, True)
    comps = ComponentRegistry(settings)

    tts = TextToSpeach(comps, settings)
    tts.say("Text1", "en")
    tts.say("Text2", "en")
    # TODO: Test commented out - does not work in continous testing environment
    # Probably need VLC or sound hw???
    # currently i don't know a direct way to test this.
    # the text will take ~3 secs to play
    # while tts._tts_thread.is_alive():
    #     time.sleep(1)
    #     i += 1
    # assert i > 2


def testOnSoundDisabled(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(SOUND_ENABLED, False)
    comps = ComponentRegistry(settings)

    tts = TextToSpeach(comps, settings)
    tts.say("Text1", "en")
    # not a very good method of testing
    assert not tts._tts_thread.is_alive()
