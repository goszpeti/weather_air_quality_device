import os
import platform

from test.conftest import mock_run_on_target, mock_run_on_non_target

def test_init_on_non_target(base_fixture, mocker):
    mock_run_on_non_target(mocker)
    from waqd.base.system import RuntimeSystem
    from waqd.base.network import Network

    # This test expects, that it is NOT run on a Raspberry Pi
    cur_system = RuntimeSystem()
    assert not cur_system.is_target_system
    if platform.system == "Linux": # works only on linux
        assert not cur_system.platform is None



def test_init_on_target(base_fixture, mocker):
    # Mocks call to get info of Rpi
    mock_run_on_target(mocker)
    from waqd.base.system import RuntimeSystem
    cur_system = RuntimeSystem()
    assert cur_system.is_target_system
    # Actual string is platform dependent
    assert cur_system.platform == "RASPBERRY PI 4B"

def test_shutdown(base_fixture, mocker):
    mock_run_on_target(mocker)
    from waqd.base.system import RuntimeSystem
    mocker.patch('os.system')
    cur_system = RuntimeSystem()
    cur_system.shutdown()
    # not ideal: confidence through duplication
    os.system.assert_called_once_with(
        'shutdown now')  # pylint: disable=no-member


def test_restart(base_fixture, mocker):
    from waqd.base.system import RuntimeSystem

    mock_run_on_target(mocker)
    mocker.patch('os.system')
    cur_system = RuntimeSystem()
    cur_system.restart()
    # not ideal: confidence through duplication
    os.system.assert_called_once_with(
        'shutdown -r now')  # pylint: disable=no-member
