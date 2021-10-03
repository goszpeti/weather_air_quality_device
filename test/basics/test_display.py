from time import sleep
from waqd.components.display import Display

def testStartupBrigthtnessSet(base_fixture):
    disp = Display("anytype", brightness=70)

    sleep(1) # wait for the brightness to be set

    # check if brightness was set
    assert disp.get_brightness() == 70
