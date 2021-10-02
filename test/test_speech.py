from waqd.components.speech import TextToSpeach
from waqd.settings import SOUND_ENABLED, Settings
from waqd.base.components import ComponentRegistry

import time


def testTTSParallel(base_fixture, capsys):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(SOUND_ENABLED, True)
    comps = ComponentRegistry(settings)

    tts = TextToSpeach(comps, "en")
    tts.say("Text1")
    tts.say("Text2")

    tts.wait_for_tts()
    # we can implicitly check, if the Thread has been started by us
    assert "TTS" in tts._tts_thread.getName() 
    # test that no warning was thrown
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert "Sound: Cannot play sound" not in captured.out

def testOnSoundDisabled(base_fixture, capsys):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(SOUND_ENABLED, "en")
    comps = ComponentRegistry(settings)

    tts = TextToSpeach(comps, settings)
    tts.say("Text1", "en")
    tts.wait_for_tts()
    # we can implicitly check, if the Thread has been started by us
    assert "TTS" in tts._tts_thread.getName()
    # test that no warning was thrown
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert "Sound: Cannot play sound" not in captured.out
