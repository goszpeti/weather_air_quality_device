"""
This test starts the application.
It is called z_integration, so that it launches last.
"""

import sys
import time
import pytest

from subprocess import Popen


@pytest.mark.integration
def test_debug_disabled_for_release():
    import waqd
    assert waqd.DEBUG_LEVEL == 0  # debug level should be 0 for release


@pytest.mark.integration
def test_version_number_valid():
    from waqd import __version__ as VERSION
    from distutils.version import StrictVersion as Version
    assert Version(VERSION)


@pytest.mark.integration
def test_smoke(base_fixture):
    backup = sys.argv
    sys.argv = []

    proc = Popen([sys.executable, str(base_fixture.base_path / "src" / "waqd" / "__main__.py")])
    time.sleep(20)
    assert proc.poll() is None  # checks that it still runs
    proc.terminate()
    time.sleep(3)
    assert proc.poll() != 0  # terminate exits os dependently, but never with success (0)
    sys.argv = backup
