import os
import platform

from test.conftest import mock_run_on_target, mock_run_on_non_target

def testInitOnNonTarget(base_fixture, mocker):
    mock_run_on_non_target(mocker)
    from waqd.base.system import RuntimeSystem
    from waqd.base.network import Network

    # This test expects, that it is NOT run on a Raspberry Pi
    cur_system = RuntimeSystem()
    assert not cur_system.is_target_system
    if platform.system == "Linux": # works only on linux
        assert not cur_system.platform is None

    [ip4, _] = Network().get_ip()
    assert not ip4 is None


def testInitOnTarget(base_fixture, mocker):
    # Mocks call to get info of Rpi
    mock_run_on_target(mocker)
    from waqd.base.system import RuntimeSystem
    cur_system = RuntimeSystem()
    assert cur_system.is_target_system
    # Actual string is platform dependent
    assert cur_system.platform == "RASPBERRY PI 4B"

def testShutdown(base_fixture, mocker):
    mock_run_on_target(mocker)
    from waqd.base.system import RuntimeSystem
    mocker.patch('os.system')
    cur_system = RuntimeSystem()
    cur_system.shutdown()
    # not ideal: confidence through duplication
    os.system.assert_called_once_with(
        'shutdown now')  # pylint: disable=no-member


def testRestart(base_fixture, mocker):
    from waqd.base.system import RuntimeSystem

    mock_run_on_target(mocker)
    mocker.patch('os.system')
    cur_system = RuntimeSystem()
    cur_system.restart()
    # not ideal: confidence through duplication
    os.system.assert_called_once_with(
        'shutdown -r now')  # pylint: disable=no-member


def testGetIPOnTarget(base_fixture, mocker):
    mock_run_on_target(mocker)
    from waqd.base.system import RuntimeSystem
    cur_system = RuntimeSystem()
    from waqd.base.network import Network

    ip4_ref = "192.168.1.274"
    ip6_ref = "2001:db8:85a3:8d3:1319:8a2e:370:7348"
    mock_call = mocker.Mock()

    # check only ip4
    mock_call.return_value = ip4_ref.encode("utf-8")
    mocker.patch('subprocess.check_output', mock_call)
    [ip4, ip6] = Network().get_ip()
    assert ip4 == ip4_ref
    assert ip6 == ""

    # check only ip6
    mock_call.return_value = ip6_ref.encode("utf-8")
    mocker.patch('subprocess.check_output', mock_call)
    [ip4, ip6] = Network().get_ip()
    assert ip4 == ""
    assert ip6 == ip6_ref

    # check both ip4 and ip6
    mock_call.return_value = (ip4_ref + " " + ip6_ref).encode("utf-8")
    mocker.patch('subprocess.check_output', mock_call)
    [ip4, ip6] = Network().get_ip()
    assert ip4 == ip4_ref
    assert ip6 == ip6_ref
