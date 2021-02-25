from piweather.components.display import Display
from piweather.settings import BRIGHTNESS, Settings

def testStartupBrigthtnessSet(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(BRIGHTNESS, 70)
    disp = Display(settings)

    # check if brightness was set
    assert disp.get_brightness() == 70
