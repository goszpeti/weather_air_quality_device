import os

from piweather.base.system import RuntimeSystem
from .conftest import mock_run_on_target


def testInitOnNonTarget(base_fixture):
    # This test expects, that it is NOT run on a Raspberry Pi
    cur_system = RuntimeSystem()
    assert not cur_system.is_target_system
    # Actual string is platform dependent
    assert not cur_system.platform is None

    [ip4, _] = cur_system.get_ip()
    assert not ip4 is None


def testInitOnTarget(base_fixture, mocker):
    # Mocks call to get info of Rpi
    mock_platform = mock_run_on_target(mocker)
    cur_system = RuntimeSystem()
    assert cur_system.is_target_system
    # Actual string is platform dependent
    assert cur_system.platform == mock_platform.return_value


def testShutdown(base_fixture, mocker):
    # TODO this would be really cool in Docker with an actual system
    mock_run_on_target(mocker)
    mocker.patch('os.system')
    cur_system = RuntimeSystem()
    cur_system.shutdown()
    # not ideal: confidence through duplication
    os.system.assert_called_once_with(
        'shutdown now')  # pylint: disable=no-member


def testRestart(base_fixture, mocker):
    # TODO this would be really cool in Docker with an actual system
    mock_run_on_target(mocker)
    mocker.patch('os.system')
    cur_system = RuntimeSystem()
    cur_system.restart()
    # not ideal: confidence through duplication
    os.system.assert_called_once_with(
        'shutdown -r now')  # pylint: disable=no-member


def testGetIPOnTarget(base_fixture, mocker):
    # TODO this would be really cool in Docker with an actual system
    mock_run_on_target(mocker)
    cur_system = RuntimeSystem()

    ip4_ref = "192.168.1.274"
    ip6_ref = "2001:db8:85a3:8d3:1319:8a2e:370:7348"
    mock_call = mocker.Mock()

    # check only ip4
    mock_call.return_value = ip4_ref.encode("utf-8")
    mocker.patch('subprocess.check_output', mock_call)
    [ip4, ip6] = cur_system.get_ip()
    assert ip4 == ip4_ref
    assert ip6 is None

    # check only ip6
    mock_call.return_value = ip6_ref.encode("utf-8")
    mocker.patch('subprocess.check_output', mock_call)
    [ip4, ip6] = cur_system.get_ip()
    assert ip4 is None
    assert ip6 == ip6_ref

    # check both ip4 and ip6
    mock_call.return_value = (ip4_ref + " " + ip6_ref).encode("utf-8")
    mocker.patch('subprocess.check_output', mock_call)
    [ip4, ip6] = cur_system.get_ip()
    assert ip4 == ip4_ref
    assert ip6 == ip6_ref
