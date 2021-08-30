from time import sleep
from waqd.components.display import Display
from waqd.settings import BRIGHTNESS, Settings

def testStartupBrigthtnessSet(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(BRIGHTNESS, 70)
    disp = Display(settings)

    sleep(1) # wait for the brightness to be set

    # check if brightness was set
    assert disp.get_brightness() == 70
